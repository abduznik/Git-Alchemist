import os
import time
import re
from datetime import datetime
from typing import Optional, Tuple
from rich.console import Console
from rich.prompt import Confirm
from .core import generate_content
from .utils import run_shell, parse_json_response
from .env import validate_gh_auth

console = Console()

def get_open_issues() -> str:
    """Fetches a list of open issues from the repository."""
    try:
        issues_json = run_shell('gh issue list --state open --limit 20 --json number,title', check=False)
        if not issues_json:
            return "No open issues found."
        
        import json
        issues = json.loads(issues_json)
        if not issues:
             return "No open issues found."
             
        formatted = "\n".join([f"#{i['number']}: {i['title']}" for i in issues])
        return formatted
    except Exception:
        return "Could not fetch issues (gh cli error)."

def get_branch_diff(base_branch: str = "master") -> Tuple[Optional[str], str]:
    """Gets the diff between the current branch and the base branch."""
    try:
        # If base_branch is not provided or invalid, try to detect it
        if not base_branch:
             remote_info = run_shell("git remote show origin", check=False)
             if remote_info:
                 for line in remote_info.splitlines():
                     if "HEAD branch" in line:
                         base_branch = line.split(":")[-1].strip()
                         break
             if not base_branch:
                 base_branch = "master"
             
        return run_shell(f"git diff {base_branch}...HEAD", check=False), base_branch
    except Exception:
        return None, "master"

def handle_uncommitted_changes(mode: str = "fast") -> bool:
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
Constraint: Max 70 characters. No quotes. Start with a verb (e.g., 'fix:', 'feat:', 'chore:')
"""
        commit_msg = generate_content(prompt, mode=mode)
        if commit_msg:
            # Basic cleanup for commit message: strip markdown blocks and quotes
            commit_msg = re.sub(r'```(?:[a-zA-Z]+)?', '', commit_msg).strip()
            commit_msg = commit_msg.replace('```', '').strip()
            commit_msg = commit_msg.strip().replace('"', '').replace("'", "")
            # Ensure it's a single line if possible or just handle newlines safely
            commit_msg = commit_msg.split('\n')[0].strip()
        else:
            commit_msg = f"wip: auto-commit changes {timestamp}"

    # Commit
    run_shell(f'git commit -m "{commit_msg}"')
    console.print(f"[green]Committed changes:[/green] {commit_msg}")
    
    return True

def forge_pr(mode: str = "fast") -> None:
    """
    Analyzes changes (committed or uncommitted) and opens a professional PR on GitHub.
    """
    username = validate_gh_auth()
    if not username:
        return

    # Handle uncommitted changes first
    handle_uncommitted_changes(mode=mode)

    # Detect base branch
    base_branch = None
    remote_info = run_shell("git remote show origin", check=False)
    if remote_info:
        for line in remote_info.splitlines():
            if "HEAD branch" in line:
                base_branch = line.split(":")[-1].strip()
                break
    
    if not base_branch:
        base_branch = "master"
    
    diff, base = get_branch_diff(base_branch)
    
    if not diff:
        console.print("[yellow]No changes detected between current branch and base branch.[/yellow]")
        return

    console.print(f"[cyan]Forging Pull Request details for branch relative to {base}...[/cyan]")
    
    # Fetch context
    open_issues = get_open_issues()
    current_branch = run_shell("git rev-parse --abbrev-ref HEAD")
    
    prompt = f"""
Task: Generate a professional GitHub Pull Request title and technical description.
Context: 
- Current Branch: {current_branch}
- Open Issues:
{open_issues}

DIFF:
'''
{diff[:5000]}
'''

Instructions:
1. Title: Concise, semantic (e.g., feat: add X, fix: handle Y).
2. Body: 
   - Start DIRECTLY with the high-level description/summary (Do NOT use a header like 'Summary' or '## Summary').
   - Follow with a section "## Technical Changes" with bullet points.
3. **CRITICAL**: The output MUST be a valid JSON object with keys:
   - "title": (string) PR Title
   - "body": (string) PR Body
   - "fixes_issue": (number or null) If the code resolves an open issue, put the issue number here.

Example Output:
{{
  "title": "feat: add new feature",
  "body": "This PR adds...\n\n## Technical Changes\n* Change A\n* Change B",
  "fixes_issue": 42
}}
"""

    result = generate_content(prompt, mode=mode)
    if not result:
        return

    try:
        pr_data = parse_json_response(result)
        if not pr_data or not isinstance(pr_data, dict):
            # Fallback: Maybe the AI just gave us the text directly
            clean_text = re.sub(r'```(?:[a-zA-Z]+)?', '', result).strip()
            clean_text = clean_text.replace('```', '').strip()
            lines = clean_text.split('\n', 1)
            if len(lines) >= 2:
                pr_data = {"title": lines[0].strip(), "body": lines[1].strip()}
            else:
                pr_data = {"title": lines[0].strip(), "body": clean_text[:100]}
        
        title = pr_data.get("title", "AI PR Update")
        body = pr_data.get("body", "Automated PR created by Git-Alchemist.")
        
        # Explicitly append "Fixes #..." if detected
        issue_num = pr_data.get("fixes_issue")
        if issue_num and isinstance(issue_num, int):
            body += f"\n\nFixes #{issue_num}"
        
        console.print(f"\n[bold green]Forged PR Title:[/bold green] {title}")
        console.print(f"[bold green]Forged PR Body:[/bold green]\n{body}\n")
        
        if os.getenv("FORGE_NO_CONFIRM") or Confirm.ask("Forge and open this PR on GitHub?"):
            # Ensure branch is pushed
            console.print(f"[gray]Pushing {current_branch} to origin...[/gray]")
            run_shell(f"git push -u origin {current_branch} --force")
            
            # Create PR
            cmd = f'gh pr create --title "{title}" --body "{body}\n\n> Forged by Git-Alchemist ⚗️"'
            output = run_shell(cmd)
            if output and output.startswith("http"):
                console.print(f"[bold yellow]✨ PR successfully forged and opened: {output}[/bold yellow]")
            else:
                 console.print("[bold yellow]✨ PR successfully forged and opened![/bold yellow]")
                 if output: console.print(f"[dim]{output}[/dim]")

            # Cleanup: Checkout base branch and delete the forge branch
            try:
                # Ensure we have the latest base branch
                console.print(f"[gray]Returning to {base.strip()}...[/gray]")
                run_shell(f"git checkout {base.strip()}")
                run_shell(f"git pull origin {base.strip()}", check=False)
                
                if current_branch != base.strip():
                    console.print(f"[gray]Deleting local branch {current_branch}...[/gray]")
                    run_shell(f"git branch -D {current_branch}")
                    console.print(f"[green]Cleanup complete: Switched to {base.strip()} and deleted {current_branch}.[/green]")
            except Exception as cleanup_error:
                 console.print(f"[yellow]Warning: Cleanup failed ({cleanup_error}). You may still be on the forge branch.[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Failed to forge PR:[/red] {e}")
        console.print(f"[gray]Raw AI response:[/gray] {result}")