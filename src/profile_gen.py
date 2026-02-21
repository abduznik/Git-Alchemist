import os
import json
import tempfile
import shutil
import re
from pathlib import Path
from typing import List, Literal, Dict, Any
from rich.console import Console
from rich.prompt import Confirm
from .core import generate_content
from .utils import run_shell, check_gh_auth, get_user_email
from .types import RepoMetadata

console = Console()

def fetch_repos(username: str) -> List[RepoMetadata]:
    """
    Fetches public repositories for the user.
    """
    console.print("[cyan]Fetching repositories...[/cyan]")
    cmd = 'gh repo list --visibility=public --limit 100 --json name,description,url,isPrivate,isArchived,stargazerCount'
    try:
        output = run_shell(cmd)
        if not output:
            return []
        raw_data = json.loads(output)
        if not isinstance(raw_data, list):
            console.print("[red]Unexpected JSON structure from gh CLI[/red]")
            return []
        
        repos = []
        for item in raw_data:
            try:
                repos.append(RepoMetadata.from_dict(item))
            except Exception as e:
                console.print(f"[yellow]Skipping malformed repo data: {e}[/yellow]")
        return repos
    except Exception as e:
        console.print(f"[red]Failed to fetch repos:[/red] {e}")
        return []

def filter_repos(
    repos: List[RepoMetadata], 
    username: str, 
    strategy: Literal["FULL_GEN", "SMART_UPDATE"]="FULL_GEN", 
    existing_content: str = ""
) -> List[RepoMetadata]:
    """
    Filters out junk, private, archived, and irrelevant repos (like Awesome lists).
    """
    candidates = []
    
    # Blocklist for low-value repos
    junk_patterns = ["test", "export", "WPy64", "PROFILE_DRAFT.md", "temp", "awesome-"]
    
    for r in repos:
        name = r.name
        
        # Basic filters
        if name == username: continue
        if r.isPrivate: continue
        if r.isArchived: continue
        if any(p in name.lower() for p in junk_patterns): continue
        if name.endswith(".exe"): continue
        
        # Strategy filter
        if strategy == "SMART_UPDATE":
            # Check if name or URL exists in current profile content
            if name in existing_content or r.url in existing_content:
                continue
        
        candidates.append(r)
        
    return candidates

def generate_profile(
    username: str, 
    force: bool = False, 
    mode: Literal["fast", "smart"]="fast"
) -> None:
    """
    Main function to generate or update the profile.
    """
    if not username:
        username = check_gh_auth()
        if not username:
            console.print("[red]Not logged into GitHub CLI. Run 'gh auth login' first.[/red]")
            return

    console.print(f"[green]Authenticated as: {username}[/green]")
    
    # Discovery
    current_content = ""
    strategy: Literal["FULL_GEN", "SMART_UPDATE"] = "FULL_GEN"
    
    try:
        console.print("[cyan]Checking for existing profile...[/cyan]")
        current_content = run_shell(f'gh api "repos/{username}/{username}/readme" --headers "Accept: application/vnd.github.raw"', check=False)
        if current_content and len(current_content) > 200 and not force:
            console.print("[green]Found existing robust profile. Switching to SMART_UPDATE.[/green]")
            strategy = "SMART_UPDATE"
        else:
             console.print("[yellow]Profile basic or missing. Using FULL_GEN.[/yellow]")
    except:
        pass

    # Fetch & Filter
    repos = fetch_repos(username)
    candidates = filter_repos(repos, username, strategy, current_content)
    
    if not candidates:
        console.print("[green]No new repositories to add.[/green]")
        return

    # Prompt Engineering
    candidates_str = "\n".join([f"- Name: {r.name}\n  Desc: {r.description or ''}\n  URL: {r.url}" for r in candidates])
    
    prompt = ""
    full_context = ""
    
    if strategy == "SMART_UPDATE":
        prompt = f"""
Task: Update a GitHub Profile README.
Instructions:
1. Integrate the 'New Projects' into the 'Existing Markdown' naturally.
2. Place them under appropriate categories.
3. PRESERVE THE EXISTING STRUCTURE: Do not delete existing sections, badges, or headers.
4. MANDATORY LINKING: Use the provided URL for each project in the format '- **[Name](URL)** - Description'.
5. MATCH THE STYLE: If the existing list uses bullets, stick to it.
6. STRICTLY NO EMOJIS in new additions.
7. Output the FULL updated Markdown content.
"""
        full_context = f"Existing Markdown:\n'''\n{current_content}\n'''\n\nNew Projects to Add:\n{candidates_str}"
        
    else:
        # Full Gen
        prompt = f"""
Task: Generate a professional Project Showcase for a GitHub Profile.
Username: {username}

Instructions:
1. Group projects into 3-6 meaningful categories (e.g., '## AI & Automation', '## Hardware').
2. MANDATORY LINKING: Use the format '- **[Name](URL)** - Description'.
3. Use a clean, professional header at the top.
4. STRICTLY NO EMOJIS.
5. Output the FULL Markdown.
"""
        full_context = f"Projects List:\n{candidates_str}"

    console.print(f"[magenta]Generating content with Gemini ({mode} mode)...[/magenta]")
    # Pass combined context
    result = generate_content(prompt, mode=mode, context=full_context)
    
    if not result:
        return

    # Post-processing
    final_md = result.replace("```markdown", "").replace("```", "").strip()
    
    # Ensure branding is preserved but clean
    footer = "\n\n---\n*Generated by Git-Alchemist ⚗️*"
    if "*Generated by Git-Alchemist*" not in final_md:
        final_md += footer

    # Save Draft
    with open("PROFILE_DRAFT.md", "w", encoding="utf-8") as f:
        f.write(final_md)
    console.print(f"[magenta]Draft saved to PROFILE_DRAFT.md[/magenta]")
    
    # Deploy (Strictly PR)
    if Confirm.ask("Deploy these changes via Pull Request?"):
        deploy_profile(username, final_md)

def deploy_profile(username: str, content: str) -> None:
    """
    Clones the profile repo, updates README, and opens a PR.
    """
    temp_dir = tempfile.mkdtemp(prefix="git_alchemist_")
    try:
        console.print("[cyan]Cloning profile repository...[/cyan]")
        run_shell(f'gh repo clone {username}/{username} {temp_dir}')
        
        # Determine the target dir (sometimes gh clones into a subdir, sometimes not)
        repo_dir = Path(temp_dir)
        if (repo_dir / username).exists():
            repo_dir = repo_dir / username
            
        # Write file
        readme_path = repo_dir / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Git ops
        cwd = os.getcwd()
        os.chdir(repo_dir)
        
        branch_name = f"profile-update-{os.urandom(2).hex()}"
        run_shell(f'git checkout -b {branch_name}')
        
        user_email = get_user_email() or f"{username}@users.noreply.github.com"
        run_shell(f'git config user.name "{username}"')
        run_shell(f'git config user.email "{user_email}"')
        
        run_shell('git add README.md')
        run_shell(f'git commit -m "docs: Update profile README via Git-Alchemist"')
        run_shell(f'git push -u origin {branch_name} --force')
        
        console.print("[green]Opening PR...[/green]")
        run_shell(f'gh pr create --title "AI Profile Update" --body "Automated profile update generated by Git-Alchemist. Added missing repo links and organized new projects."')
        
        os.chdir(cwd)
        
    except Exception as e:
        console.print(f"[red]Deployment failed:[/red] {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
