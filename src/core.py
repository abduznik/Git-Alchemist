import os
import sys
import time
from google import genai
from dotenv import load_dotenv
from rich.console import Console

console = Console()

# Define model tiers based on your available list
SMART_MODELS = [
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-1.5-pro", # Fallback to stable if preview fails
]

FAST_MODELS = [
    "gemma-3-27b-it",
    "gemma-3-12b-it",
    "gemini-3-flash-preview",
    "gemini-2.0-flash",
]

def get_gemini_client():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[yellow]Warning:[/yellow] GEMINI_API_KEY not found. Using Mock AI mode.")
        return None
    return genai.Client(api_key=api_key, http_options={'api_version':'v1alpha'})

def generate_content(prompt, mode="fast"):
    """
    Generates content with automatic fallback.
    Mode: 'fast' (Gemma/Flash) or 'smart' (Pro/3-Pro)
    """
    client = get_gemini_client()
    
    if client is None:
        # Mock responses for testing without API key
        if "JSON" in prompt or "title" in prompt.lower():
             return '```json\n{"title": "Forge Feature Update", "body": "This is an automated PR forged by Git-Alchemist (Mock Mode)."}\n```'
        return "chore: update readme with forge feature"

    models = SMART_MODELS if mode == "smart" else FAST_MODELS
    
    for model_name in models:
        try:
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
                console.print(f"[yellow]Quota hit for {model_name}. Trying next...[/yellow]")
                continue
            else:
                console.print(f"[red]Error with {model_name}:[/red] {err_msg}")
                continue
                
    console.print("[bold red]Critical:[/bold red] All models exhausted or failed.")
    return None