import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from typing import Any, List, Optional
from dataclasses import dataclass
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .env import validate_environment

console = Console()

# User-specified model tiers
SMART_MODELS = [
    "gemini-3-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

FAST_MODELS = [
    "gemma-3-27b-it",
    "gemma-3-12b-it",
    "gemma-3-4b-it",
]

# Safe token limits
SAFE_TOKEN_LIMIT_FAST = 12000
SAFE_TOKEN_LIMIT_SMART = 230000 

# Heuristic: ~4 characters per token
CHARS_PER_TOKEN = 4

@dataclass
class GenerationConfig:
    timeout: int = 60
    api_version: str = "v1beta"

def validate_prompt(prompt: str) -> None:
    """Basic validation for the prompt."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

def get_gemini_client() -> str:
    """Returns the validated API key."""
    return validate_environment()

def estimate_tokens(text: str) -> int:
    """
    Estimates token count using a simple character heuristic.
    """
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN

def split_context(context: str, limit: int) -> list[str]:
    """
    Splits context into chunks that fit within the token limit.
    """
    chunk_size = limit * CHARS_PER_TOKEN
    return [context[i:i+chunk_size] for i in range(0, len(context), chunk_size)]

def generate_with_fallback(
    api_key: str,
    prompt: str,
    models: list[str],
    silent: bool = False,
    config: GenerationConfig = GenerationConfig()
) -> str | None:
    """
    Helper to try a list of models in order using direct API calls.
    Uses headers for the API key to avoid URL exposure.
    """
    try:
        validate_prompt(prompt)
    except ValueError as e:
        if not silent:
            console.print(f"[red]Prompt validation error:[/red] {e}")
        return None
    
    for model_name in models:
        try:
            if not silent:
                console.print(f"[gray]Attempting with {model_name}...[/gray]")
            
            url = f"https://generativelanguage.googleapis.com/{config.api_version}/models/{model_name}:generateContent"
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': api_key
            }
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=config.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if 'candidates' in data and data['candidates']:
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code in [429, 503]:
                if not silent:
                    console.print(f"[yellow]Model {model_name} busy or quota hit ({status_code}). Trying next...[/yellow]")
                continue
            else:
                if not silent:
                    console.print(f"[red]HTTP Error with {model_name} ({status_code}):[/red] {e}")
                continue
        except requests.exceptions.Timeout:
            if not silent:
                console.print(f"[yellow]Timeout for {model_name} after {config.timeout}s. Trying next...[/yellow]")
            continue
        except requests.exceptions.RequestException as e:
            if not silent:
                console.print(f"[red]Request Error with {model_name}:[/red] {e}")
            continue
        except (KeyError, IndexError):
            if not silent:
                console.print(f"[red]Format Error in response from {model_name}[/red]")
            continue
                
    if not silent:
        console.print("[bold red]Critical:[/bold red] All models exhausted or failed.")
    return None

def generate_content(prompt: str, mode: str = "fast", context: str | None = None) -> str:
    """
    Generates content with strict model separation and parallel smart chunking.
    """
    api_key = get_gemini_client()
    # Strict separation: Fast uses ONLY Gemma, Smart uses ONLY Gemini
    models = SMART_MODELS if mode == "smart" else FAST_MODELS
    
    # Determine safe limit based on mode
    safe_limit = SAFE_TOKEN_LIMIT_SMART if mode == "smart" else SAFE_TOKEN_LIMIT_FAST
    
    total_tokens = estimate_tokens(prompt) + estimate_tokens(context or "")
    
    # 1. Smart Chunking (Map-Reduce) for large contexts
    if context and total_tokens > safe_limit:
        console.print(f"[yellow]Large context detected (~{total_tokens} tokens). Engaging Smart Chunking with {models[0]}...[/yellow]")
        
        chunks = split_context(context, safe_limit)
        summaries = []
        batch_size = 2 # Process 2 chunks in parallel
        
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Iterate through chunks in batches
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                futures = []
                
                console_print(f"[cyan]Processing batch {i//batch_size + 1} ({len(batch)} chunks)...[/cyan]")
                
                for chunk in batch:
                    chunk_prompt = f"""
    Analyze the following part of the codebase context based on this instruction:
    "{prompt}"    
    PARTIAL CONTEXT:
    '''
    {chunk}
    '''
    
    Extract any relevant information found in this chunk. If nothing is relevant, say "Nothing relevant".
    """
                    futures.append(executor.submit(generate_with_fallback, api_key, chunk_prompt, models, silent=True))
                
                for future in as_completed(futures):
                    try:
                        res = future.result()
                        if res and "Nothing relevant" not in res:
                            summaries.append(res)
                    except Exception as e:
                        console.print(f"[red]Chunk processing failed:[/red] {e}")

                # Delay between batches to respect rate limits (if not the last batch)
                if i + batch_size < len(chunks):
                    time.sleep(1)

        # REDUCE STEP
        if not summaries:
            return "No relevant information found in the provided context."
            
        console.print("[cyan]Synthesizing final answer...[/cyan]")
        combined_summaries = "\n".join(summaries)
        final_prompt = f"""
        Here are the findings from analyzing different parts of the codebase:
        
        {combined_summaries}
        
        Based on these findings, answer the original user request:
        {prompt}
        """
        return generate_with_fallback(api_key, final_prompt, models) or "No relevant information found in the provided context."

    # 2. Standard Generation
    full_prompt = f"{prompt}\n\nCONTEXT:\n{context}" if context else prompt
    return generate_with_fallback(api_key, full_prompt, models) or "No relevant information found in the provided context."
