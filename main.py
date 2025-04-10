from agent import TaskAgent
from rich.console import Console
from rich.prompt import Prompt

def main():
    console = Console()
    console.print("[bold blue]AI Task Agent[/bold blue]")
    console.print("Enter your task in natural language. Type 'exit' to quit.\n")
    
    agent = TaskAgent()
    
    while True:
        task = Prompt.ask("What would you like me to do?")
        
        if task.lower() in ['exit', 'quit', 'q']:
            console.print("[yellow]Goodbye![/yellow]")
            break
            
        if task.strip():
            agent.run_task(task)
        
        console.print()  # Add a blank line for better readability

if __name__ == "__main__":
    main() 