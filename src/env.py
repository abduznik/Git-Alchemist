import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from .utils import run_shell

console = Console()

def validate_environment() -> str:
    """
    Ensures GEMINI_API_KEY is set.
    Returns the API key if valid, otherwise exits.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY environment variable not found.")
        console.print("[yellow]Tip:[/yellow] Create a .env file with GEMINI_API_KEY=your_key_here")
        sys.exit(1)
    return api_key

def validate_gh_auth() -> str:
    """
    Ensures the user is authenticated with GitHub CLI.
    Returns the username if authenticated, otherwise exits.
    """
    try:
        user_login = run_shell('gh api user -q ".login"', suppress_errors=True)
        if not user_login:
            console.print("[bold red]Error:[/bold red] Not authenticated with GitHub CLI.")
            console.print("[yellow]Tip:[/yellow] Run 'gh auth login' to authenticate.")
            sys.exit(1)
        return user_login
    except Exception:
        console.print("[bold red]Error:[/bold red] GitHub CLI (gh) is not installed or not working correctly.")
        sys.exit(1)

def ensure_ready(require_gh: bool = False) -> dict:
    """
    Performs all necessary checks before starting operations.
    Returns a dictionary with validated info.
    """
    info = {
        "gemini_api_key": validate_environment()
    }
    if require_gh:
        info["gh_user"] = validate_gh_auth()
    return info
