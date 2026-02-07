import os
import time
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm
from .core import generate_content
from .utils import run_shell, check_gh_auth

console = Console()

def get_open_issues():
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
    except:
        return "Could not fetch issues (gh cli error)."

def get_branch_diff(base_branch="master"):
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
Constraint: Max 70 characters. No quotes. Start with a verb (e.g., 'fix:', 'feat:', 'chore:')
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
   - **Crucial**: If the changes likely resolve or relate to any Open Issue listed above (check branch name and code), append "Fixes #<number>" or "Relates to #<number>" at the very end.
3. **CRITICAL**: The output MUST be a valid JSON object with keys "title" and "body".

Example Output:
{{
  "title": "feat: add new feature",
  "body": "This PR adds...\n\n## Technical Changes\n* Change A\n* Change B"
}}
"""

    result = generate_content(prompt, mode=mode)
    if not result:
        return

    try:
        import json
        clean_json = result.replace("```json", "").replace("```", "").strip()
        
        # Try parsing JSON first
        try:
            pr_data = json.loads(clean_json)
        except json.JSONDecodeError:
            # Fallback: Parse "Title: ... Body: ..." format
            import re
            title_match = re.search(r"Title:\s*(.+)", clean_json, re.IGNORECASE)
            # Body is everything after "Body:"
            body_match = re.search(r"Body:\s*(.+)", clean_json, re.IGNORECASE | re.DOTALL)
            
            if title_match and body_match:
                pr_data = {
                    "title": title_match.group(1).strip(),
                    "body": body_match.group(1).strip()
                }
            else:
                # "Hail Mary" fallback: First line is title, rest is body
                lines = clean_json.split('\n', 1)
                if len(lines) >= 2:
                    pr_data = {"title": lines[0].strip(), "body": lines[1].strip()}
                else:
                    pr_data = {"title": lines[0].strip(), "body": "Automated PR."}
        
        title = pr_data.get("title", "AI PR Update")
        body = pr_data.get("body", "Automated PR created by Git-Alchemist.")
        
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
