import json
import tempfile
import os
from rich.console import Console
from .core import generate_content
from .utils import run_shell, get_codebase_context

console = Console()

def create_issue(idea, mode="fast"):
    """
    Translates an idea into technical GitHub issue(s).
    """
    # Heuristic: If the user wants to "find", "search", or "scan", we need context.
    needs_context = any(kw in idea.lower() for kw in ["find", "search", "scan", "identify", "check", "issues", "bugs", "todos", "fixme"])
    
    context = None
    if needs_context:
        console.print("[cyan]Scanning codebase context for analysis...[/cyan]")
        context = get_codebase_context()

    console.print(f"[cyan]Drafting technical issue(s) for: {idea} ({mode} mode)...[/cyan]")
    
    prompt = f"""
You are a Senior Tech Lead.
User Input: '{idea}'
TASK: Translate this into technical implementation plan(s).

Instructions:
1. Analyze the User Input.
2. If the user wants to FIND/SCAN for issues (e.g. "Find bugs", "create issues for TODOs"), use the provided CONTEXT (if any) to identify specific, actionable items.
3. If the user wants to create a SINGLE specific feature/bug report, just plan that one.
4. For "one line fixes", look for typos, simple logic errors, or missing safe-guards.

OUTPUT FORMAT:
Return ONLY a JSON **LIST** of objects. Each object must have:
- "title": concise title
- "body": detailed description with context and specific file references if available.
- "label": suggested label (e.g. "bug", "enhancement", "refactor")
- "easy": boolean (true if it's a small/starter task)

**IMPORTANT**: Use forward slashes `/` for all file paths (e.g., `src/cli.py`, not `src\cli.py`) to avoid JSON escape errors.

Example Output:
[
  {{ "title": "Fix typo in cli.py", "body": "...", "label": "bug", "easy": true }},
  {{ "title": "Refactor auth logic", "body": "...", "label": "refactor", "easy": false }}
]

No markdown blocks.
"""

    result = generate_content(prompt, mode=mode, context=context)
    if not result: return

    try:
        clean_json = result.replace("```json", "").replace("```", "").strip()
        
        # Handle cases where the LLM might return a single object or a list
        if clean_json.strip().startswith("{"):
            issues = [json.loads(clean_json)]
        else:
            issues = json.loads(clean_json)
            
        if not isinstance(issues, list):
            issues = [issues]
            
        if not issues:
             console.print("[yellow]No issues generated.[/yellow]")
             return

        console.print(f"[green]Generated {len(issues)} issue(s). Uploading...[/green]")

        success_count = 0
        for issue in issues:
            title = f"[DRAFT] {issue.get('title')}"
            body = f"{issue.get('body')}\n\n> Automated by Git-Alchemist"
            label = issue.get('label', 'enhancement')
            
            console.print(f"[yellow]Uploading Draft: {title}[/yellow]")
            
            # Create labels if they don't exist
            run_shell('gh label create "automated" --color "505050"', check=False, suppress_errors=True)
            run_shell('gh label create "status: draft" --color "333333"', check=False, suppress_errors=True)
            run_shell(f'gh label create "{label}"', check=False, suppress_errors=True)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tf:
                tf.write(body)
                temp_name = tf.name

            cmd = [
                'gh',
                'issue',
                'create',
                '--title',
                f'"{title}"',
                '--body-file',
                f'"{temp_name}"',
                '--label',
                '"status: draft"',
                '--label',
                '"automated"',
                '--label',
                f'"{label}"'
            ]
            
            if issue.get('easy'):
                run_shell('gh label create "good first issue" --color "7057ff"', check=False, suppress_errors=True)
                cmd.extend(['--label', '"good first issue"'])

            output = run_shell(" ".join(cmd))
            os.unlink(temp_name)
            
            if output and output.startswith("http"):
                success_count += 1
                console.print(f"[dim]Created: {output}[/dim]")
            else:
                console.print(f"[red]Failed to create issue: {title}[/red]")
        
        if success_count > 0:
            console.print(f"[green]Success! {success_count}/{len(issues)} issues created.[/green]")
        else:
            console.print("[red]All issue creation attempts failed.[/red]")
        
    except Exception as e:
        console.print(f"[red]Failed to create issue(s):[/red] {e}")
        console.print(f"[gray]Raw Output:[/gray] {result}")
