import os
from rich.console import Console
from rich.prompt import Prompt
from .core import generate_content
from .utils import run_shell

console = Console()

def get_staged_diff():
    """Returns the diff of staged changes."""
    return run_shell("git diff --cached", check=False)

def suggest_commits(mode="fast"):
    """
    Analyzes staged changes and suggests 3 semantic commit messages.
    """
    diff = get_staged_diff()
    
    if not diff:
        console.print("[yellow]No staged changes found.[/yellow]")
        if Prompt.ask("Stage all changes now? (git add .)", choices=["y", "n"], default="y") == "y":
            run_shell("git add .")
            diff = get_staged_diff()
        else:
            return

    console.print("[cyan]Analyzing changes for the perfect commit message...[/cyan]")
    
    prompt = f"""
Task: Suggest 3 professional, semantic commit messages based on the git diff provided in the Context.
Format: <type>(<scope>): <subject>
Types: feat, fix, docs, style, refactor, test, chore

Instructions:
1. Return ONLY a numbered list of 3 options.
2. No explanations or extra text.
3. Ensure they are concise and accurate.
"""

    # Pass diff as context
    result = generate_content(prompt, mode=mode, context=diff)
    if not result:
        return

    options = [line.strip() for line in result.strip().split("\n") if line.strip()]
    # Remove numbering if AI added it (e.g., "1. feat: ...")
    clean_options = []
    for opt in options:
        # Match "1. ", "1) ", etc.
        import re
        clean_opt = re.sub(r'^\d+[\.\)]\s*', '', opt).strip()
        if clean_opt:
            clean_options.append(clean_opt)

    console.print("\n[bold green]Recommended Transmutations:[/bold green]")
    for i, opt in enumerate(clean_options, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] {opt}")
    
    choice = Prompt.ask("\nSelect a message to commit (or 'c' to cancel)", choices=[str(i) for i in range(1, len(clean_options)+1)] + ["c"])
    
    if choice != "c":
        selected_msg = clean_options[int(choice)-1]
        console.print(f"[green]Committing with message:[/green] {selected_msg}")
        run_shell(f'git commit -m "{selected_msg}"')
    else:
        console.print("[yellow]Commit aborted.[/yellow]")