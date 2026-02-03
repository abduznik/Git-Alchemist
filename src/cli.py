import argparse
import sys
from rich.console import Console
from .profile_gen import generate_profile

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Git-Alchemist: AI-powered Git Operations")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Profile Generator Command
    profile_parser = subparsers.add_parser("profile", help="Generate or update GitHub Profile README")
    profile_parser.add_argument("--force", action="store_true", help="Force full regeneration")
    profile_parser.add_argument("--user", help="GitHub username (optional, detects automatically)")

    args = parser.parse_args()
    
    if args.command == "profile":
        generate_profile(args.user, args.force)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
