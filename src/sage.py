import os
from rich.console import Console
from .core import generate_content
from .utils import run_shell

console = Console()

def get_codebase_context():
    """
    Scans the repository and aggregates source code into a single context string.
    """
    context = []
    # Extensions to include
    extensions = {'.py', '.md', '.ps1', '.sh', '.js', '.ts', '.c', '.cpp', '.h', '.yml', '.yaml', '.Dockerfile'}
    # Folders to ignore
    ignore_dirs = {'__pycache__', '.git', 'venv', 'node_modules', '.tmp', 'docs'}

    for root, dirs, files in os.walk("."):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in extensions:
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        context.append(f"--- FILE: {path} ---\n{content}\n")
                except Exception:
                    continue
                    
    return "\n".join(context)

def ask_sage(question, mode="fast"):
    """
    Queries Gemini using the aggregated codebase as context.
    """
    console.print("[cyan]The Sage is meditating on your codebase...[/cyan]")
    
    code_context = get_codebase_context()
    
    if not code_context:
        console.print("[yellow]Warning: No source files found to analyze.[/yellow]")
        code_context = "No code found in repository."

    prompt = f"""
You are "The Sage", an expert software architect and technical lead. 
Below is the source code context for the current project. 
Use this context to answer the user's question precisely and technically.

CONTEXT:
'''
{code_context}
'''

USER QUESTION:
{question}

Instructions:
1. Base your answer ONLY on the provided code.
2. Be concise but deep.
3. If the answer isn't in the code, say so.
"""

    result = generate_content(prompt, mode=mode)
    
    if result:
        console.print("\n[bold fuchsia]--- The Sage's Wisdom ---[/bold fuchsia]")
        console.print(result)
        console.print("[bold fuchsia]-----------------------[/bold fuchsia]")
