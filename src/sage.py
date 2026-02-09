import os
from rich.console import Console
from .core import generate_content
from .utils import run_shell, get_codebase_context

console = Console()

def ask_sage(question: str, mode: str = "fast") -> None:
    """
    Queries Gemini using the aggregated codebase as context.
    """
    console.print("[cyan]The Sage is meditating on your codebase...[/cyan]")
    
    code_context = get_codebase_context()
    
    if not code_context:
        console.print("[yellow]Warning: No source files found to analyze.[/yellow]")
        code_context = "No code found in repository."

    # Prompt focuses only on the persona and the question
    prompt = f"""
You are "The Sage", an expert software architect and technical lead. 
Use the provided context to answer the user's question precisely and technically.

USER QUESTION:
{question}

Instructions:
1. Base your answer ONLY on the provided code context.
2. Be concise but deep.
3. If the answer isn't in the code, say so.
"""

    # Pass code_context separately to trigger smart chunking if needed
    result = generate_content(prompt, mode=mode, context=code_context)
    
    if result:
        console.print("\n[bold fuchsia]--- The Sage's Wisdom ---[/bold fuchsia]")
        console.print(result)
        console.print("[bold fuchsia]-----------------------[/bold fuchsia]")