from rich.console import Console
from rich.prompt import Prompt
from .core import generate_content
from .sage import get_codebase_context

console = Console()

ALCHEMIST_MANUAL = """
You are the "Alchemist Helper", an intelligent assistant for the Git-Alchemist CLI tool.
Your goal is to help the user with their project, debug issues, or guide them on how to use Git-Alchemist.

Git-Alchemist Capabilities:
- `alchemist forge`: Automatically generate and open a PR from the current branch.
- `alchemist commit`: Generate semantic commit messages from changes.
- `alchemist sage "question"`: Ask questions about the codebase.
- `alchemist audit`: Check repository 'Gold' status and metadata.
- `alchemist profile`: Generate or update GitHub Profile README.
- `alchemist topics`: Optimize repository topics/tags.
- `alchemist describe`: Generate missing repository descriptions.
- `alchemist issue "idea"`: Draft a technical issue from an idea.
- `alchemist scaffold "instruction"`: Generate a new project structure.
- `alchemist fix "file" "instruction"`: Modify a file using AI.
- `alchemist explain "context"`: Explain code or concepts.

If the user asks how to do something that one of these commands solves, recommend the specific command.
If the user asks for coding help, debugging, or structuring advice, use the provided Codebase Context.
"""

def run_helper(mode="fast"):
    """
    Interactive helper that reads codebase context and answers user queries.
    """
    console.print("[bold green]Alchemist Helper initialized.[/bold green]")
    console.print("I have read your current directory context. How can I assist you today?")
    
    # 1. Gather Context
    with console.status("[cyan]Reading directory context...[/cyan]"):
        code_context = get_codebase_context()
        if not code_context:
            code_context = "No code found in repository."

    # 2. Interactive Input
    while True:
        user_query = Prompt.ask("\n[bold yellow]You[/bold yellow]")
        
        if user_query.lower() in ["exit", "quit", "q"]:
            console.print("[green]Goodbye![/green]")
            break

        if not user_query.strip():
            continue

        # 3. Construct Prompt
        full_prompt = f"""
{ALCHEMIST_MANUAL}

CODEBASE CONTEXT:
'''
{code_context}
'''

USER QUERY:
{user_query}

Instructions:
1. Answer the user's query directly.
2. If suggesting a Git-Alchemist command, show the exact syntax.
3. Be helpful, concise, and technical.
"""

        # 4. Generate Answer
        with console.status("[magenta]Thinking...[/magenta]"):
            response = generate_content(full_prompt, mode=mode)

        if response:
            console.print("\n[bold cyan]Alchemist Helper:[/bold cyan]")
            console.print(response)
