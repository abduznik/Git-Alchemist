import os
import shutil
import subprocess

def run_shell(command, **kwargs):
    """
    Runs a shell command and returns the output.
    Accepts extra kwargs (like check=False) to pass to subprocess.run if needed.
    """
    try:
        # We manually pop 'check' if it's there to avoid double-passing issues if we changed implementation details,
        # but since we are wrapping subprocess.run, we can filter what we want or just catch errors.
        # However, subprocess.run DOES support 'check'.
        # The issue is that my previous implementation didn't accept **kwargs.
        
        # We allow 'check' to be passed, default is False essentially because we catch exceptions.
        # If the user sets check=True, the exception below will catch it and return None.
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True, **kwargs)
        return result.stdout.strip()
    except Exception as e:
        return None

def get_codebase_context():
    """
    Scans the repository and aggregates source code into a single context string.
    """
    context = []
    # Extensions to include
    extensions = {'.py', '.md', '.ps1', '.sh', '.js', '.ts', '.c', '.cpp', '.h', '.yml', '.yaml', '.Dockerfile', '.json', '.toml'}
    # Folders to ignore
    ignore_dirs = {'__pycache__', '.git', 'venv', 'node_modules', '.tmp', 'docs', 'dist', 'build', '.gemini'}

    for root, dirs, files in os.walk("."):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in extensions:
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        context.append(f"--- FILE: {path} ---\n{content}\n")
                except Exception:
                    continue
                    
    return "\n".join(context)

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