import os
import time
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm
from .core import generate_content
from .utils import run_shell, check_gh_auth

console = Console()

def get_branch_diff(base_branch="master"):
    """Gets the diff between the current branch and the base branch."""
    try:
        # If base_branch is not provided or invalid, try to detect it
        if not base_branch:
             base_branch = run_shell("git remote show origin | grep 'HEAD branch' | cut -d' ' -f5", check=False) or "master"
             
        return run_shell(f"git diff {base_branch}...HEAD", check=False), base_branch
    except:
        return None, "master"

def handle_uncommitted_changes(mode="fast"):
    """
    Checks for uncommitted changes, creates a branch, and commits them.
    Returns True if a new branch was created and changes committed.
    """
    status = run_shell("git status --porcelain", check=False)
    if not status:
        return False

    console.print("[yellow]Uncommitted changes detected. Forging a new branch...[/yellow]")
    
    # Generate unique branch name
    timestamp = int(time.time())
    new_branch = f"forge-{timestamp}"
    
    # Create and switch to new branch
    run_shell(f"git checkout -b {new_branch}")
    console.print(f"[green]Switched to new branch: {new_branch}[/green]")
    
    # Stage all changes
    run_shell("git add .")
    
    # Generate commit message
    diff = run_shell("git diff --staged", check=False)
    if not diff:
        # Fallback if diff is somehow empty or large binary
        commit_msg = f"wip: auto-commit changes {timestamp}"
    else:
        prompt = f"""
Task: Generate a concise, semantic git commit message for the following changes.
Diff:
'''
{diff[:3000]}
'''
Constraint: Max 70 characters. No quotes. Start with a verb (e.g., 'fix:', 'feat:', 'chore:').
"""
        commit_msg = generate_content(prompt, mode=mode)
        if commit_msg:
             commit_msg = commit_msg.strip().replace('"', '').replace("'", "")
        else:
             commit_msg = f"wip: auto-commit changes {timestamp}"

    # Commit
    run_shell(f'git commit -m "{commit_msg}"')
    console.print(f"[green]Committed changes:[/green] {commit_msg}")
    
    return True

def forge_pr(mode="fast"):
    """
    Analyzes changes (committed or uncommitted) and opens a professional PR on GitHub.
    """
    username = check_gh_auth()
    if not username:
        console.print("[red]Not authenticated with gh CLI.[/red]")
        return

    # Handle uncommitted changes first
    handle_uncommitted_changes(mode=mode)

    # Detect base branch
    base_branch = run_shell("git remote show origin | grep 'HEAD branch' | cut -d' ' -f5", check=False) 
    if not base_branch:
        base_branch = "master"
        # Try main if master doesn't look right, but remote show origin is best source
        # or check local branches
    
    diff, base = get_branch_diff(base_branch)
    
    # If no diff, maybe we are on the base branch and just committed?
    # get_branch_diff compares base...HEAD. If we are on a new branch that branched from base, it should work.
    
    if not diff:
        console.print("[yellow]No changes detected between current branch and base branch.[/yellow]")
        return

    console.print(f"[cyan]Forging Pull Request details for branch relative to {base}...[/cyan]")
    
    prompt = f"""
Task: Generate a professional GitHub Pull Request title and technical description.
Context: Below is the git diff for the current branch.

DIFF:
'''
{diff[:5000]}
'''

Instructions:
1. Title: Concise, semantic (e.g., feat: add X, fix: handle Y).
2. Body: 
   - **Summary**: 1-2 sentences on what this PR does.
   - **Technical Changes**: Bullet points explaining the logic changes.
3. Return ONLY a JSON object with "title" and "body" keys. No markdown blocks.
"""

    result = generate_content(prompt, mode=mode)
    if not result:
        return

    try:
        import json
        clean_json = result.replace("```json", "").replace("```", "").strip()
        pr_data = json.loads(clean_json)
        
        title = pr_data.get("title", "AI PR Update")
        body = pr_data.get("body", "Automated PR created by Git-Alchemist.")
        
        console.print(f"\n[bold green]Forged PR Title:[/bold green] {title}")
        console.print(f"[bold green]Forged PR Body:[/bold green]\n{body}\n")
        
        if os.getenv("FORGE_NO_CONFIRM") or Confirm.ask("Forge and open this PR on GitHub?"):
            # Ensure branch is pushed
            current_branch = run_shell("git rev-parse --abbrev-ref HEAD")
            console.print(f"[gray]Pushing {current_branch} to origin...[/gray]")
            run_shell(f"git push -u origin {current_branch} --force")
            
            # Create PR
            cmd = f'gh pr create --title "{title}" --body "{body}\n\n> Forged by Git-Alchemist ⚗️"'
            run_shell(cmd)
            console.print("[bold yellow]✨ PR successfully forged and opened![/bold yellow]")
            
    except Exception as e:
        console.print(f"[red]Failed to forge PR:[/red] {e}")
        console.print(f"[gray]Raw AI response:[/gray] {result}")
