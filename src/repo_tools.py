import json
import time
from typing import Optional, Literal
from rich.console import Console
from .core import generate_content
from .utils import run_shell, check_gh_auth

console = Console()

def optimize_topics(user: Optional[str] = None, mode: Literal["fast", "smart"] = "fast") -> None:
    """
    Analyzes repositories and adds relevant topics using Gemini.
    """
    username = user or check_gh_auth()
    if not username:
        console.print("[red]Not authenticated with gh CLI.[/red]")
        return

    console.print(f"[cyan]Optimizing topics for {username} ({mode} mode)...[/cyan]")
    repos_raw = run_shell('gh repo list --visibility=public --limit 100 --json name,description,repositoryTopics')
    repos = json.loads(repos_raw)

    count = 0
    for repo in repos:
        name = repo['name']
        desc = repo.get('description') or "No description provided"
        
        # Safe access to topics
        raw_topics = repo.get('repositoryTopics')
        if raw_topics is None:
            existing = []
        else:
            existing = [t['name'] for t in raw_topics]
        
        if len(existing) >= 5:
            continue

        console.print(f"[white]Analyzing {name}...[/white]")
        
        prompt = f"""
Task: Suggest search-friendly GitHub topics for project "{name}". 
Description: "{desc}". 
Existing Topics: {existing}. 
Return ONLY a JSON array of strings (max 5 total topics). 
Focus on technical keywords like 'python', 'api', 'automation', 'cli'.
Output Example: ["python", "automation"]
"""
        result = generate_content(prompt, mode=mode)
        if not result: continue

        try:
            clean_json = result.replace("```json", "").replace("```", "").strip()
            new_tags = json.loads(clean_json)
            
            # Filter out existing
            to_add = [t for t in new_tags if t not in existing]
            
            if to_add:
                tag_str = ",".join(to_add)
                console.print(f"  [green]Adding tags:[/green] {tag_str}")
                run_shell(f'gh repo edit {username}/{name} --add-topic "{tag_str}"')
                count += 1
                time.sleep(0.5)
        except:
            console.print(f"  [red]Failed to parse topics for {name}[/red]")

    console.print(f"[cyan]Done! Optimized {count} repositories.[/cyan]")

def generate_descriptions(user: Optional[str] = None, mode: Literal["fast", "smart"] = "fast") -> None:
    """
    Generates descriptions for repositories that are missing them.
    """
    username = user or check_gh_auth()
    if not username: return

    console.print(f"[cyan]Generating descriptions for {username} ({mode} mode)...[/cyan]")
    repos_raw = run_shell('gh repo list --visibility=public --limit 100 --json name,description')
    repos = json.loads(repos_raw)

    count = 0
    for repo in repos:
        name = repo['name']
        if name == username: continue # Skip profile repo
        if repo.get('description'): continue # Skip if already has desc

        console.print(f"[white]Analyzing {name}...[/white]")
        
        # Fetch Readme
        try:
            # We fetch the whole readme now, allowing the engine to chunk if needed
            readme = run_shell(f'gh repo view {username}/{name} --json body -q .body', check=False)
            context = readme if readme else "No readme available."
        except:
            context = "No readme available."

        prompt = f"""
Task: Generate a GitHub repository description for project "{name}". 
Constraint: Max 20 words. Start with an action verb. 
Output ONLY the description. No quotes.
"""
        # Pass readme as context
        result = generate_content(prompt, mode=mode, context=context)
        if not result: continue

        new_desc = result.strip().replace('"', '').replace("'", "")
        if len(new_desc) > 200: new_desc = new_desc[:197] + "..."

        console.print(f"  [green]New Desc:[/green] {new_desc}")
        run_shell(f'gh repo edit {username}/{name} --description "{new_desc}"')
        count += 1
        time.sleep(0.5)

    console.print(f"[cyan]Done! Updated {count} descriptions.[/cyan]")