import os
import shutil
import subprocess
import sys
import json
import re
from typing import Any 

def run_shell(command: str, suppress_errors: bool = False, **kwargs: Any) -> str | None:
    """
    Runs a shell command and returns the output.
    Accepts extra kwargs (like check=False) to pass to subprocess.run if needed.
    Forces UTF-8 encoding to avoid Windows CP1252 errors.
    
    Args:
        command (str): The shell command to execute.
        suppress_errors (bool): If True, stderr will not be printed on failure.
    """
    try:
        # Force UTF-8 encoding for input and output to handle special characters/emojis
        kwargs['encoding'] = 'utf-8'
        kwargs['errors'] = 'replace' # Replace invalid characters instead of crashing
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True, **kwargs)
        
        if result.returncode != 0 and result.stderr and not suppress_errors:
             # Print error to stderr so the user can see it even if we return stdout
             print(f"[Shell Error] Command: {command}", file=sys.stderr)
             print(f"[Shell Error] Details: {result.stderr.strip()}", file=sys.stderr)

        return result.stdout.strip()
    except Exception as e:
        if not suppress_errors:
            print(f"[Shell Exception] {e}", file=sys.stderr)
        return None

def parse_json_response(result: str | None) -> Any | None:
    """
    Attempts to parse a JSON object from a string, handling common issues like
    markdown code blocks and partial JSON.
    """
    if not result:
        return None

    # 1. Strip markdown blocks
    # Handles ```json ... ```, ``` ... ```, and even just ``` at the start/end
    clean_result = re.sub(r'```(?:json)?', '', result).strip()
    clean_result = clean_result.replace('```', '').strip()

    # 2. Try direct load
    try:
        return json.loads(clean_result)
    except json.JSONDecodeError:
        # 3. Last ditch effort: Try to find everything between first { and last }
        # or first [ and last ]
        try:
            match = re.search(r'(\{.*\}|\[.*\])', clean_result, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # 4. If all fails, print error and return None
        print(f"[JSON Parse Error] Failed to parse: {str(result)[:100]}...", file=sys.stderr)
        return None

def get_codebase_context() -> str:
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

def check_gh_auth() -> str | None:
    """
    Checks if the user is authenticated with GitHub CLI.
    Returns the username if authenticated, else None.
    """
    try:
        user_login = run_shell('gh api user -q ".login"')
        return user_login
    except:
        return None

def get_user_email() -> str | None:
    """
    Gets the user email from GitHub CLI.
    """
    try:
        email = run_shell('gh api user -q ".email"', check=False)
        return email if email else None
    except:
        return None
