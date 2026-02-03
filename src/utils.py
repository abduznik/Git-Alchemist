import subprocess
import json
import shutil
from rich.console import Console

console = Console()

def run_shell(command, check=True, capture_output=True):
    """
    Runs a shell command and returns the result.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if check:
            console.print(f"[bold red]Command Failed:[/bold red] {command}")
            console.print(f"[red]Error:[/red] {e.stderr}")
            raise e
        return None

def check_gh_auth():
    """
    Checks if the user is authenticated with GitHub CLI.
    Returns the username if authenticated, else None.
    """
    try:
        user_login = run_shell('gh api user -q ".login"')
        return user_login
    except:
        return None

def get_user_email():
    """
    Gets the user email from GitHub CLI.
    """
    try:
        email = run_shell('gh api user -q ".email"', check=False)
        return email if email else None
    except:
        return None
