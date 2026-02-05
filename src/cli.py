import argparse
import sys
from rich.console import Console
from .profile_gen import generate_profile
from .architect import scaffold_project, fix_code, explain_code
from .repo_tools import optimize_topics, generate_descriptions
from .issue_gen import create_issue
from .audit import run_audit
from .sage import ask_sage
from .committer import suggest_commits
from .forge import forge_pr
from .helper import run_helper

console = Console()

def main():
    # Parent parser for global arguments like --smart
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--smart", action="store_true", help="Use high-end Gemini Pro models (slower/lower quota)")

    parser = argparse.ArgumentParser(description="Git-Alchemist: AI-powered Git Operations")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Helper Command
    helper_parser = subparsers.add_parser("helper", parents=[parent_parser], help="Interactive assistant for project help and tool usage")

    # Forge Command
    forge_parser = subparsers.add_parser("forge", parents=[parent_parser], help="Automatically generate and open a PR from the current branch")

    # Commit Command
    commit_parser = subparsers.add_parser("commit", parents=[parent_parser], help="Generate semantic commit messages from changes")

    # Sage Command
    sage_parser = subparsers.add_parser("sage", parents=[parent_parser], help="Ask the Sage questions about your codebase")
    sage_parser.add_argument("question", help="The question about your code")

    # Audit Command
    audit_parser = subparsers.add_parser("audit", parents=[parent_parser], help="Check repository 'Gold' status and metadata")
    audit_parser.add_argument("--repo", help="Specific repository name to audit")

    # Profile Generator Command
    profile_parser = subparsers.add_parser("profile", parents=[parent_parser], help="Generate or update GitHub Profile README")
    profile_parser.add_argument("--force", action="store_true", help="Force full regeneration")
    profile_parser.add_argument("--user", help="GitHub username (optional, detects automatically)")

    # Repo Tools
    topics_parser = subparsers.add_parser("topics", parents=[parent_parser], help="Optimize repository topics/tags")
    topics_parser.add_argument("--user", help="GitHub username")

    describe_parser = subparsers.add_parser("describe", parents=[parent_parser], help="Generate missing repository descriptions")
    describe_parser.add_argument("--user", help="GitHub username")

    # Issue Generator
    issue_parser = subparsers.add_parser("issue", parents=[parent_parser], help="Draft a technical issue from an idea")
    issue_parser.add_argument("idea", help="The feature or bug idea")

    # Architect Commands
    scaffold_parser = subparsers.add_parser("scaffold", parents=[parent_parser], help="Generate a new project structure (safe mode)")
    scaffold_parser.add_argument("instruction", help="What to build (e.g., 'A Flask app with Docker')")

    fix_parser = subparsers.add_parser("fix", parents=[parent_parser], help="Modify a file using AI")
    fix_parser.add_argument("file", help="Path to the file to fix")
    fix_parser.add_argument("instruction", help="What to change")

    explain_parser = subparsers.add_parser("explain", parents=[parent_parser], help="Explain code or concepts")
    explain_parser.add_argument("context", help="The code or concept to explain")

    args = parser.parse_args()
    
    # Check if a command was selected
    if not args.command:
        parser.print_help()
        return

    mode = "smart" if args.smart else "fast"
    
    if args.command == "profile":
        generate_profile(args.user, args.force, mode=mode)
    elif args.command == "topics":
        optimize_topics(args.user, mode=mode)
    elif args.command == "describe":
        generate_descriptions(args.user, mode=mode)
    elif args.command == "issue":
        create_issue(args.idea, mode=mode)
    elif args.command == "scaffold":
        scaffold_project(args.instruction, mode=mode)
    elif args.command == "fix":
        fix_code(args.file, args.instruction, mode=mode)
    elif args.command == "explain":
        explain_code(args.context, mode=mode)
    elif args.command == "audit":
        run_audit(repo_name=args.repo)
    elif args.command == "sage":
        ask_sage(args.question, mode=mode)
    elif args.command == "commit":
        suggest_commits(mode=mode)
    elif args.command == "forge":
        forge_pr(mode=mode)
    elif args.command == "helper":
        run_helper(mode=mode)

if __name__ == "__main__":
    main()