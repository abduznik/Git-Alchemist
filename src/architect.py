import os
import json
import shutil
import tempfile
import subprocess
from rich.console import Console
from rich.prompt import Confirm
from .core import generate_content
from .utils import run_shell

console = Console()

def scaffold_project(instruction, mode="fast"):
    """
    Generates shell commands to scaffold a project in a temporary directory.
    """
    console.print(f"[cyan]Architecting solution for: {instruction} ({mode} mode)...[/cyan]")
    
    # Create temp env
    temp_dir = tempfile.mkdtemp(prefix="git_alchemist_scaffold_")
    console.print(f"[gray]Created temporary workspace: {temp_dir}[/gray]")
    
    prompt = f"""
Task: Project Scaffolding.
User Goal: "{instruction}"
Operating System: Linux/Unix (Termux)
Constraint: Return ONLY a JSON object with a single key "commands" containing an array of shell strings.
The commands should assume they are running INSIDE the project root.
Example: {{'commands': ['mkdir src', 'touch src/main.py', "echo 'print(1)' > src/main.py"]}}
Do NOT use markdown blocks.
"""

    result = generate_content(prompt, mode=mode)
    if not result:
        shutil.rmtree(temp_dir)
        return

    try:
        clean_result = result.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_result)
        commands = data.get("commands", [])
        
        console.print("[green]Generated Plan:[/green]")
        for cmd in commands:
            console.print(f"  > {cmd}")
            
        if Confirm.ask("Execute these commands in the temporary workspace?"):
            # Execute in temp dir
            cwd = os.getcwd()
            os.chdir(temp_dir)
            try:
                for cmd in commands:
                    console.print(f"[cyan]Running:[/cyan] {cmd}")
                    run_shell(cmd)
                
                console.print("[green]Scaffolding complete in temporary workspace.[/green]")
                console.print(f"[gray]Contents of {temp_dir}:[/gray]")
                run_shell("ls -R")
                
                if Confirm.ask("Keep these files? (Moves them to current directory)"):
                    # Move files from temp_dir to cwd
                    for item in os.listdir(temp_dir):
                        s = os.path.join(temp_dir, item)
                        d = os.path.join(cwd, item)
                        if os.path.exists(d):
                            console.print(f"[yellow]Warning:[/yellow] {item} already exists in current directory. Skipping.")
                        else:
                            shutil.move(s, d)
                    console.print("[green]Files moved successfully.[/green]")

                    # NEW: Auto-Deployment Logic
                    if Confirm.ask("Initialize Git and deploy to GitHub?"):
                        repo_name = os.path.basename(os.getcwd())
                        console.print(f"[cyan]Initializing repository: {repo_name}...[/cyan]")
                        
                        # 1. Initialize and set identity if missing
                        run_shell("git init")
                        try:
                            run_shell("git config user.name", check=True)
                        except:
                            run_shell(f'git config user.name "abduznik"')
                            run_shell(f'git config user.email "abduznik@users.noreply.github.com"')

                        # 2. Add and Commit
                        run_shell("git add .")
                        run_shell('git commit -m "feat: Initial scaffold by Git-Alchemist"')
                        
                        # 3. Create and Push
                        try:
                            console.print("[magenta]Creating GitHub repository...[/magenta]")
                            run_shell(f"gh repo create {repo_name} --public --source=. --remote=origin --push")
                            console.print(f"[bold yellow]✨ Project deployed to GitHub: {repo_name}[/bold yellow]")
                        except Exception as e:
                            console.print(f"[red]GitHub deployment failed:[/red] {e}")
                else:
                    console.print("[yellow]Discarding workspace.[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]Execution failed:[/red] {e}")
            finally:
                os.chdir(cwd)
        
    except json.JSONDecodeError:
        console.print(f"[red]Failed to parse AI response:[/red] {result}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            console.print("[gray]Temporary workspace cleaned up.[/gray]")

def fix_code(file_path, instruction, mode="fast"):
    """
    Reads a file, applies an AI fix, and optionally creates a PR.
    """
    if not os.path.exists(file_path):
        console.print(f"[red]File not found:[/red] {file_path}")
        return

    console.print(f"[cyan]Reading {file_path} ({mode} mode)...[/cyan]")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    prompt = f"""
Task: Fix/Modify Code.
User Instructions:
'''
{instruction}
'''

Target File Content is provided in the Context.

Goal: Return ONLY the complete, corrected file content based on the User Instructions. Do not use markdown blocks.
"""
    
    console.print(f"[magenta]Consulting Gemini ({mode} mode)...[/magenta]")
    # Pass content as context to enable smart chunking if file is huge
    result = generate_content(prompt, mode=mode, context=content)
    if not result:
        return

    clean_result = result.replace("```python", "").replace("```", "").strip() # Generic cleanup
    
    # Backup
    backup_path = f"{file_path}.bak"
    shutil.copy(file_path, backup_path)
    console.print(f"[gray]Backup created: {backup_path}[/gray]")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(clean_result)
        
    console.print(f"[green]File updated.[/green]")
    
    if Confirm.ask("Create a PR for this fix?"):
        # This assumes we are in a git repo
        try:
            branch_name = f"fix/ai-{os.urandom(4).hex()}"
            run_shell(f"git checkout -b {branch_name}")
            run_shell(f"git add {file_path}")
            run_shell(f'git commit -m "AI Fix: {instruction}"')
            run_shell(f"git push -u origin {branch_name}")
            run_shell(f'gh pr create --title "AI Fix: {instruction}" --body "Automated fix." --web')
        except Exception as e:
            console.print(f"[red]PR creation failed:[/red] {e}")

def explain_code(context, mode="fast"):
    """
    Explains a concept or code snippet.
    """
    prompt = f"Task: Explain Concept/Code. Context is provided. Keep it concise and technical."
    # Pass context separately
    result = generate_content(prompt, mode=mode, context=context)
    if result:
        console.print(f"\n[bold white]--- Explanation ---[/bold white]\n{result}\n[bold white]-------------------[/bold white]")