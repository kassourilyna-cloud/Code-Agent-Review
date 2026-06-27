import subprocess
import json
from typing import List, Literal
from pydantic import BaseModel
from google import genai
from google.genai import types
from ddgs import DDGS
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

console = Console()

# Initialize the modern Google GenAI Client
client = genai.Client()
MODEL_NAME = "gemini-2.5-flash"#or "gemini-2.5-flash-lite"

class CodeIssue(BaseModel):
    location: str 
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    explanation: str
    suggestion: str

class ReviewResult(BaseModel):
    issues: List[CodeIssue]

def run_ruff(file_path: str) -> str:
    """Runs Ruff linting deterministically (Low-agentic execution)."""
    console.print("\n  [bold green][LOCAL ENGINE][/bold green] Executing static analysis: [underline]run_ruff[/underline]")
    try:
        result = subprocess.run(
            ["ruff", "check", file_path, "--format=json"], 
            capture_output=True, 
            text=True
        )
        return result.stdout if result.stdout.strip() else "[]"
    except FileNotFoundError:
        return "Error: The 'ruff' CLI engine is not installed or available on this system."

def run_bandit(file_path: str) -> str:
    """Runs Bandit security scanning deterministically (Low-agentic execution)."""
    console.print("  [bold green][LOCAL ENGINE][/bold green] Executing security scan: [underline]run_bandit[/underline]")
    try:
        result = subprocess.run(
            ["bandit", "-f", "json", "-r", file_path], 
            capture_output=True, 
            text=True
        )
        return result.stdout if result.stdout.strip() else "{}"
    except FileNotFoundError:
        return "Error: The 'bandit' CLI engine is not installed or available on this system."
    
def search_the_web(query: str) -> str:
    """Searches the internet via DuckDuckGo. High-agentic tool: Gemini decides when to use this."""
    console.print(f"\n  [bold magenta][TOOL INVOCATION][/bold magenta] Gemini triggered search: [underline]{query}[/underline]")
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
        return json.dumps(results)
    except Exception as e:
        return f"Failed to search the web: {str(e)}"    


def run_agentic_review(target_file: str):
    with open(target_file, "r") as f:
        raw_code = f.read()

    # LOW AGENTIC STEP
    ruff_results = run_ruff(target_file)
    bandit_results = run_bandit(target_file)

    # Tool mapping dictionary
    available_tools = {
        "search_the_web": search_the_web
    }

    # HIGH AGENTIC STEP
    config_tools = types.GenerateContentConfig(
        system_instruction=(
            "You are a critical, hyper-vigilant Python Code Review Agent. "
            "You have been provided the source code alongside the raw logs of Ruff and Bandit static scanners. "
            "Your job is to identify ALL potential issues, logic traps, and security flaws. Do not stop at just one. "
            "Review the logs carefully. If you are suspicious of any design pattern or library quirk, "
            "use the `search_the_web` tool to verify. Keep track of all distinct bugs found."
        ),
        tools=[search_the_web],
        max_output_tokens=2048
    )
    
    chat = client.chats.create(model=MODEL_NAME, config=config_tools)

    console.log("[yellow] Feeding data to Gemini for deep evaluation and dynamic searching...[/yellow]")
    
    initial_prompt = (
        f"Target file path: '{target_file}'\n\n"
        f"### SOURCE CODE:\n```python\n{raw_code}\n```\n\n"
        f"### RUFF STATIC LINTER OUTPUT (JSON):\n{ruff_results}\n\n"
        f"### BANDIT SECURITY SCANNER OUTPUT (JSON):\n{bandit_results}\n\n"
        f"Please analyze these inputs completely. Note every single bug, formatting issue, or vulnerability you find."
    )

    response = chat.send_message(initial_prompt)

    # Handle dynamic web searches if requested by Gemini
    if response.function_calls:
        for function_call in response.function_calls:
            tool_name = function_call.name
            tool_args = function_call.args
            
            console.log(f" [bold cyan]Agent called tool:[/bold cyan] {tool_name} with parameters: {tool_args}")
            
            if tool_name in available_tools:
                try:
                    tool_output = available_tools[tool_name](**tool_args)
                except Exception as e:
                    tool_output = f"Error processing tool: {str(e)}"

                response = chat.send_message(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": tool_output}
                    )
                )

    console.log("[yellow] Compiling data into structured format...[/yellow]")
    
    # Build a temporary standalone history sequence for structural extraction config
    structuring_history = list(chat.get_history())
    structuring_history.append(
        types.Content(
            role="user", 
            parts=[types.Part.from_text(
                text="Synthesize ALL findings discussed, including ALL individual issues identified by the tools and your analysis, "
                     "into the exact structured review schema format. Do not omit any issues."
            )]
        )
    )

    structuring_config = types.GenerateContentConfig(
        system_instruction=config_tools.system_instruction,
        response_mime_type="application/json",
        response_schema=ReviewResult,
        temperature=0.1
    )
    
    final_structured_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=structuring_history,
        config=structuring_config
    )

    try:
        report: ReviewResult = final_structured_response.parsed
        return report.issues, chat
    except Exception as e:
        console.log(f"[red]Failed schema compliance extraction.[/red] Raw data: {final_structured_response.text}")
        return [], chat

def display_report(issues, file_name):
    """Prints the final structured report in a beautiful table."""
    if not issues:
        console.print(f"\n[bold green]✨ Clean scan! No issues found in {file_name}.[/bold green]")
        return
        
    table = Table(title=f" Code Review Report: {file_name}", expand=True)
    table.add_column("Location", style="cyan", no_wrap=True) 
    table.add_column("Severity", justify="center")
    table.add_column("Explanation", style="white", no_wrap=False) 
    table.add_column("Suggestion", style="green",  no_wrap=False)  

    for issue in issues:
        # Extract strict string formatting to prevent empty token assignments inside Rich layout engines
        sev = str(issue.severity).upper().strip() if issue.severity else "LOW"
        
        if "CRITICAL" in sev:
            sev_str = "[bold magenta]CRITICAL[/bold magenta]"
        elif "HIGH" in sev:
            sev_str = "[bold red]HIGH[/bold red]"
        elif "MEDIUM" in sev or "MED" in sev:
            sev_str = "[bold yellow]MEDIUM[/bold yellow]"
        else:
            sev_str = "[bold blue]LOW[/bold blue]"

        table.add_row(
            str(issue.location),
            sev_str,
            str(issue.explanation),
            str(issue.suggestion)
        )

    console.print("\n")
    console.print(table)

def main():
    if len(sys.argv) < 2:
        console.print("[red]Error:[/red] Please provide a file to review.")
        console.print("Usage: python agent.py <path_to_messy_file.py>")
        return

    target_file = sys.argv[1]
    
    if not os.path.exists(target_file):
        console.print(f"[red]Error:[/red] File '{target_file}' not found.")
        return

    console.print(Panel(f"[bold magenta]Starting Gemini Hybrid Code Review (Deterministic + Agentic Search)[/bold magenta]\nTarget: [underline]{target_file}[/underline]", expand=False))

    with Live(console=console, refresh_per_second=4) as live:
        live.update("[bold yellow] Initializing AI Studio Pipeline...[/bold yellow]")
        issues, chat = run_agentic_review(target_file)
        
    display_report(issues, target_file)
    
    # INJECT TABLE CONTEXT INTO CHAT SESSION
    # sync the chat memory so the agent knows exactly what the user sees in the table
    if issues:
        summary_of_table = "System Note: For reference, here is the final structured table of issues presented to the user:\n"
        for idx, issue in enumerate(issues, 1):
            summary_of_table += f"Bug #{idx} ({issue.severity}) at {issue.location}: {issue.explanation}. Suggestion: {issue.suggestion}\n"
        
        # Append this as a system/user guide alignment turn
        chat.send_message(summary_of_table)
    

    console.print("\n[bold cyan] Chat session opened! Ask questions about the review or ask for code fixes (Type 'exit' to quit).[/bold cyan]")
    
    while True:
        try:
            user_input = console.input("\n[bold blue]You ──► [/bold blue]")
            if user_input.strip().lower() == "exit":
                console.print("[yellow]Goodbye![/yellow]")
                break
                
            if not user_input.strip():
                continue

            with console.status("[yellow] Agent is thinking...[/yellow]", spinner="dots"):
                chat_turn_config = types.GenerateContentConfig(max_output_tokens=2048)
                response = chat.send_message(user_input, config=chat_turn_config)
                
                #CHAT LOOP TOOL HANDLING CRITICAL ADDITION 
                # Loop to handle dynamic tool calls if Gemini decides it needs to search during chat
                while response.function_calls:
                    for function_call in response.function_calls:
                        tool_name = function_call.name
                        tool_args = function_call.args
                        
                        console.log(f" [bold cyan]Agent called tool in chat:[/bold cyan] {tool_name} with parameters: {tool_args}")
                        
                        if tool_name in available_tools:
                            try:
                                tool_output = available_tools[tool_name](**tool_args)
                            except Exception as e:
                                tool_output = f"Error processing tool: {str(e)}"

                            # Send tool output back to the model to continue the conversation stream
                            response = chat.send_message(
                                types.Part.from_function_response(
                                    name=tool_name,
                                    response={"result": tool_output}
                                )
                            )

                
            console.print(f"\n[bold magenta]Agent ──►[/bold magenta] {response.text}")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting chat session...[/yellow]")
            break
if __name__ == "__main__":
    main()
    main()