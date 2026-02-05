import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from dotenv import load_dotenv
from rich.console import Console

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

# Safe token limit for a single request (leaving room for output)
SAFE_TOKEN_LIMIT = 12000 
# Heuristic: ~4 characters per token
CHARS_PER_TOKEN = 4

def get_gemini_client():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not found.")
        sys.exit(1)
    return genai.Client(api_key=api_key, http_options={'api_version':'v1alpha'})

def estimate_tokens(text):
    """
    Estimates token count using a simple character heuristic.
    """
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN

def split_context(context, limit=SAFE_TOKEN_LIMIT):
    """
    Splits context into chunks that fit within the token limit.
    """
    chunk_size = limit * CHARS_PER_TOKEN
    return [context[i:i+chunk_size] for i in range(0, len(context), chunk_size)]

def process_chunk(client, chunk, prompt, models):
    """
    Worker function to process a single chunk.
    """
    chunk_prompt = f"""
    Analyze the following part of the codebase context based on this instruction:
    "{prompt}"
    
    PARTIAL CONTEXT:
    '''
    {chunk}
    '''
    
    Extract any relevant information found in this chunk. If nothing is relevant, say "Nothing relevant".
    """
    return generate_with_fallback(client, chunk_prompt, models, silent=True)

def generate_content(prompt, mode="fast", context=None):
    """
    Generates content with strict model separation and parallel smart chunking.
    """
    client = get_gemini_client()
    # Strict separation: Fast uses ONLY Gemma, Smart uses ONLY Gemini
    models = SMART_MODELS if mode == "smart" else FAST_MODELS
    
    total_tokens = estimate_tokens(prompt) + estimate_tokens(context)
    
    # 1. Smart Chunking (Map-Reduce) for large contexts
    if context and total_tokens > SAFE_TOKEN_LIMIT:
        console.print(f"[yellow]Large context detected (~{total_tokens} tokens). Processing with {models[0]}...[/yellow]")
        
        chunks = split_context(context)
        summaries = []
        batch_size = 2 # Process 2 chunks in parallel
        
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Iterate through chunks in batches
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                futures = []
                
                console.print(f"[cyan]Processing batch {i//batch_size + 1} ({len(batch)} chunks)...[/cyan]")
                
                for chunk in batch:
                    futures.append(executor.submit(process_chunk, client, chunk, prompt, models))
                
                for future in as_completed(futures):
                    try:
                        res = future.result()
                        if res and "Nothing relevant" not in res:
                            summaries.append(res)
                    except Exception as e:
                        console.print(f"[red]Chunk processing failed:[/red] {e}")

                # Delay between batches to respect rate limits (if not the last batch)
                if i + batch_size < len(chunks):
                    console.print("[gray]Pausing briefly for rate limits...[/gray]")
                    time.sleep(2)

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
        return generate_with_fallback(client, final_prompt, models)

    # 2. Standard Generation
    full_prompt = f"{prompt}\n\nCONTEXT:\n{context}" if context else prompt
    return generate_with_fallback(client, full_prompt, models)

def generate_with_fallback(client, prompt, models, silent=False):
    """
    Helper to try a list of models in order.
    """
    for model_name in models:
        try:
            if not silent:
                console.print(f"[gray]Attempting with {model_name}...[/gray]")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                if not silent:
                    console.print(f"[yellow]Quota/TPM hit for {model_name}. Trying next...[/yellow]")
                continue
            else:
                if not silent:
                    console.print(f"[red]Error with {model_name}:[/red] {err_msg}")
                continue
                
    if not silent:
        console.print("[bold red]Critical:[/bold red] All models exhausted or failed.")
    return None