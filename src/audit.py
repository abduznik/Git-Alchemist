import os
import json
from typing import Optional, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from .utils import run_shell, check_gh_auth

console = Console()

def run_audit(user: Optional[str] = None, repo_name: Optional[str] = None) -> Optional[int]:
    """
    Audits a repository for 'Gold Standard' items and returns a score.
    """
    username = user or check_gh_auth()
    if not username:
        console.print("[red]Not authenticated with gh CLI.[/red]")
        return None

    # Use current directory if no repo specified
    target_repo = repo_name or run_shell("gh repo view --json name --jq .name", check=False)
    if not target_repo:
        console.print("[yellow]Not inside a Git repository. Auditing current directory files only.[/yellow]")
        repo_data: dict[str, Any] = {}
    else:
        console.print(f"[cyan]Auditing Repository:[/cyan] [bold]{username}/{target_repo}[/bold]")
        repo_data_raw = run_shell(f"gh repo view {username}/{target_repo} --json description,repositoryTopics,licenseInfo", check=False)
        repo_data = json.loads(repo_data_raw) if repo_data_raw else {}

    checks = {
        "README.md": {"score": 20, "found": os.path.exists("README.md")},
        "LICENSE": {"score": 10, "found": bool(repo_data.get("licenseInfo")) or any(os.path.exists(f) for f in ["LICENSE", "LICENSE.md", "LICENSE.txt"])},
        "CONTRIBUTING.md": {"score": 10, "found": any(os.path.exists(f) for f in ["CONTRIBUTING.md", "CONTRIBUTING"])},
        "Metadata: Description": {"score": 20, "found": bool(repo_data.get("description"))},
        "Metadata: Topics": {"score": 20, "found": len(repo_data.get("repositoryTopics") or []) >= 3},
        "CI/CD: GitHub Actions": {"score": 20, "found": os.path.exists(".github/workflows")},
    }

    total_score = sum(c["score"] for c in checks.values() if c["found"])
    
    # Display Table
    table = Table(title=f"Repository Audit: {target_repo or 'Local'}", border_style="blue")
    table.add_column("Criterion", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Weight", justify="right")

    for name, data in checks.items():
        status = "[green]GOLD[/green]" if data["found"] else "[red]LEAD[/red]"
        table.add_row(name, status, f"{data['score']}")

    console.print(table)
    
    # Final Score Display
    color = "green" if total_score >= 80 else "yellow" if total_score >= 50 else "red"
    console.print(f"\n[bold]Transmutation Score:[/bold] [{color}]{total_score}%[/{color}]")
    
    if total_score < 100:
        console.print(f"\n[italic gray]The Alchemist suggests adding the missing components to reach 100% Gold.[/italic gray]")
    else:
        console.print(f"\n[bold yellow]✨ Pure Gold! This repository is optimized for the community.[/bold yellow]")

    return total_score
