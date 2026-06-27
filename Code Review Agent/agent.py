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
# It automatically picks up GEMINI_API_KEY from your environment variables
client = genai.Client()
MODEL_NAME = "gemini-2.5-flash-lite"

class CodeIssue(BaseModel):
    location: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    explanation: str
    suggestion: str

class ReviewResult(BaseModel):
    issues: List[CodeIssue]

def run_ruff(file_path: str) -> str:
    """Runs Ruff linting and returns the results as a JSON string."""
    console.print("\n  [bold magenta][TOOL INVOCATION][/bold magenta] Gemini triggered local engine: [underline]run_ruff[/underline]")
    
    try:
        result = subprocess.run(
              ["ruff", "check", file_path, "--format=json"], 
              capture_output=True, 
              text=True
        )
        return result.stdout
    except FileNotFoundError:
        return "Error: The 'ruff' CLI engine is not installed or available on this system's PATH variable."
        
    try:
        data = json.loads(result.stdout)
        return json.dumps(data)
    except json.JSONDecodeError:
        return "[]"

def run_bandit(file_path: str) -> str:
    """Runs Bandit security scanning and returns results as a JSON string."""
    console.print("\n [bold magenta][TOOL INVOCATION][/bold magenta] Gemini triggered local engine: [underline]run_bandit[/underline]")
    
    try:
        result = subprocess.run(
               ["bandit", "-f", "json", "-r", file_path], 
               capture_output=True, 
               text=True
        )
        return result.stdout
    except FileNotFoundError:
        return "Error: The 'ruff' CLI engine is not installed or available on this system's PATH variable."
        
    try:
        data = json.loads(result.stdout)
        return json.dumps(data)
    except json.JSONDecodeError:
        return "{}"
    
def search_the_web(query: str) -> str:
    """Searches the internet via DuckDuckGo to look up Python documentation, framework bugs, or security rules."""
    console.print("\n  [bold magenta][TOOL INVOCATION][/bold magenta] Gemini triggered local engine: [underline]search_the_web[/underline]")
    

    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
        return json.dumps(results)
    except Exception as e:
        return f"Failed to search the web: {str(e)}"    


def run_agentic_review(target_file: str):
    with open(target_file, "r") as f:
        raw_code = f.read()

    # Tool mapping dictionary
    available_tools = {
        "run_ruff": run_ruff,
        "run_bandit": run_bandit,
        "search_the_web": search_the_web
    }

    # Step 1: Initialize Chat History for tool execution
    # System instructions are set inside the chat configuration object in GenAI SDK
    config_tools = types.GenerateContentConfig(
        system_instruction=(
            "You are a critical, hyper-vigilant Python Code Review Agent. "
            "IMPORTANT: Local static linters like Ruff and Bandit ONLY check for basic syntax and obvious legacy flaws. "
            "They completely miss logical errors, runtime exceptions, and complex third-party library version bugs. "
            "If Ruff and Bandit return clean results (empty outputs), you MUST treat the file with higher suspicion. "
            "Use `search_the_web` to actively investigate specific error codes, complex runtime exceptions, or "
            "library patterns found in the source code before confirming your final report."
        
        ),
        tools=[run_ruff, run_bandit, search_the_web],
        max_output_tokens=350
    )
    
    chat = client.chats.create(model=MODEL_NAME, config=config_tools)

    console.log("[yellow] Agent is evaluating code and deciding on tools...[/yellow]")
    
    # Prompt the agent to start inspecting the raw string file
    response = chat.send_message(
        f"Please perform an initial tool execution assessment on this python file. Target file path: '{target_file}'\n\n```python\n{raw_code}\n```"
    )

    # Check if Gemini requested to use any tools
    if response.function_calls:
        for function_call in response.function_calls:
            tool_name = function_call.name
            tool_args = function_call.args
            
            console.log(f" [bold cyan]Agent called tool:[/bold cyan] {tool_name} with parameters: {tool_args}")
            
            if tool_name in available_tools:
                try:
                    # Dynamically execute our mapping function using arguments from Gemini
                    tool_output = available_tools[tool_name](**tool_args)
                except TypeError:
                    # Fallback argument safety catcher
                    if tool_name in ["run_ruff", "run_bandit"]:
                        tool_output = available_tools[tool_name](file_path=target_file)
                    else:
                        tool_output = "Error: Invalid tool arguments provided by model."

                # Send tool execution results back into the Gemini chat session pipeline
                response = chat.send_message(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": tool_output}
                    )
                )

    console.log("[yellow] Compiling dynamic data into Pydantic structured format...[/yellow]")
    
    # Step 2: Request structured extraction over chat memory
    # We construct a unique configuration enforcing our Pydantic Model Output structure
    structuring_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ReviewResult,
        temperature=0.1 # Keep it focused on translation rather than creativity
    )
    
    # Get total combined conversation history from our chat instance
    pure_history =list(chat.get_history())
    
    # Append a clean, closing prompt requesting the final Pydantic translation
    pure_history.append(
        types.Content(
            role="user", 
            parts=[types.Part.from_text(text="Synthesize all findings from our tool executions into the exact structured review schema format.")]
        )
    )
    # Run the schema generation using the temporary snapshot
    final_structured_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=pure_history, # Passes the copy
        config=structuring_config
    )

    final_structured_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=history,
        config=structuring_config
    )

    # Validate output structure
    try:
        # response.parsed returns the mapped Pydantic object automatically! No manual json parsing needed.
        report: ReviewResult = final_structured_response.parsed
        return report.issues,chat
    except Exception as e:
        console.log(f"[red]Failed schema compliance extraction.[/red] Raw data: {final_structured_response.text}")
        return [],chat

def display_report(issues, file_name):
    """Prints the final structured report in a beautiful table."""
    if not issues:
        console.print(f"\n[bold green]✨ Clean scan! No issues found in {file_name}.[/bold green]")
        return
    table = Table(title=f" Code Review Report: {file_name}", expand=True)
    table.add_column("Location", style="cyan",width=20, no_wrap=True) 
    table.add_column("Severity", style="bold", width=12,justify="center")
    table.add_column("Explanation", style="white",width=50, no_wrap=False) 
    table.add_column("Suggestion", style="green", width=50,no_wrap=False)  


    for issue in issues:
        sev = issue.severity.upper()
        if "HIGH" in sev or "CRIT" in sev:
            sev_str = f"[red]{sev}[/red]"
        elif "MED" in sev:
            sev_str = f"[yellow]{sev}[/yellow]"
        else:
            sev_str = f"[blue]{sev}[/blue]"

        table.add_row(
            issue.location,
            sev_str,
            issue.explanation,
            issue.suggestion
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

    console.print(Panel(f"[bold magenta]Starting Gemini Agentic Code Review[/bold magenta]\nTarget: [underline]{target_file}[/underline]", expand=False))

    with Live(console=console, refresh_per_second=4) as live:
        live.update("[bold yellow] Initializing AI Studio Pipeline...[/bold yellow]")
        issues , chat = run_agentic_review(target_file)
        
    display_report(issues, target_file)
    # 2. Open the Interactive Chat Window
    console.print("\n[bold cyan] Chat session opened! Ask questions about the review or ask for code fixes (Type 'exit' to quit).[/bold cyan]")
    
    while True:
        try:
            user_input = console.input("\n[bold blue]You ──► [/bold blue]")
            if user_input.strip().lower() == "exit":
                console.print("[yellow]Goodbye![/yellow]")
                break
                
            if not user_input.strip():
                continue

            # Send your follow-up message directly to the existing chat session history
            with console.status("[yellow] Agent is thinking...[/yellow]", spinner="dots"):
                response = chat.send_message(user_input)
                
            console.print(f"\n[bold magenta]Agent ──►[/bold magenta] {response.text}")
            
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()