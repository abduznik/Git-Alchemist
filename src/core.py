import os
import sys
from google import genai
from dotenv import load_dotenv
from rich.console import Console

console = Console()

def get_gemini_client():
    """
    Initializes and returns the Gemini Client.
    Checks for GEMINI_API_KEY in environment variables.
    """
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not found in environment variables.")
        console.print("Please set it in your .env file or export it in your shell.")
        sys.exit(1)
        
    try:
        client = genai.Client(api_key=api_key, http_options={'api_version':'v1alpha'})
        return client
    except Exception as e:
        console.print(f"[bold red]Failed to initialize Gemini Client:[/bold red] {e}")
        sys.exit(1)

def generate_content(prompt, model="gemini-2.0-flash"):
    """
    Wrapper for generating content to handle errors gracefully.
    """
    client = get_gemini_client()
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text
    except Exception as e:
        console.print(f"[bold red]Generation Error:[/bold red] {e}")
        return None
