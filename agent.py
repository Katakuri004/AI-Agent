import os
import subprocess
import re
import requests
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from dotenv import load_dotenv
from code_generator import CodeGenerator

# Load environment variables
load_dotenv()

class TaskAgent:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.console = Console()
        self.code_generator = CodeGenerator(self.api_url, self.api_key)

    def generate_plan(self, task: str) -> list:
        """Generate a plan for executing the task."""
        # Check if this is a Python script creation task
        if any(keyword in task.lower() for keyword in ['python', 'script', 'code', 'program', '.py', 'file']):
            # Extract the filename from the task or use a default
            filename = 'script.py'
            import re
            match = re.search(r'in a file called ["\']?([^"\']+)["\']?', task)
            if match:
                filename = match.group(1)
            else:
                # Try to find any .py file mentioned
                py_match = re.search(r'["\']?([^"\']+\.py)["\']?', task)
                if py_match:
                    filename = py_match.group(1)
            
            # Create a plan for Python script creation
            return [
                {
                    "description": f"Create Python script: {filename}",
                    "command": f"python -c \"print('Creating {filename}...')\""
                },
                {
                    "description": f"Generate and write code to {filename}",
                    "command": f"python -c \"from code_generator import CodeGenerator; import os; generator = CodeGenerator('{self.api_url}', '{self.api_key}'); generator.create_script_file('{task}', '{filename}')\""
                },
                {
                    "description": f"Check the contents of {filename}",
                    "command": f"type {filename}"
                },
                {
                    "description": f"Run the {filename} script",
                    "command": f"python {filename}"
                }
            ]
        
        # For non-Python tasks, use the regular plan generation
        prompt = f"""<s>[INST] Create a step-by-step plan to execute this task: {task}

For each step, provide:
1. A clear description of what needs to be done
2. The exact command to execute (if applicable)

Example format:
1. Step description: Create a Python script
   Command: python script.py

2. Step description: Run the script
   Command: python script.py

Keep the plan simple and focused on the task. Only include executable commands, not instructions. [/INST]</s>"""

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 1000,
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "return_full_text": False
                    }
                },
                timeout=30
            )
            
            response.raise_for_status()
            plan_text = response.json()[0]["generated_text"].strip()
            
            # Parse the plan into steps
            steps = []
            current_step = None
            
            for line in plan_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Check for step number
                step_match = re.match(r'^\d+\.\s*(.*)', line)
                if step_match:
                    if current_step:
                        steps.append(current_step)
                    current_step = {"description": step_match.group(1).strip(), "command": None}
                elif current_step and "command:" in line.lower():
                    current_step["command"] = line.split(":", 1)[1].strip()
            
            if current_step:
                steps.append(current_step)
            
            # Filter out steps without commands
            steps = [step for step in steps if step.get("command")]
            
            return steps
            
        except Exception as e:
            self.console.print(f"[red]Error generating plan: {str(e)}[/red]")
            return []

    def execute_command(self, command: str) -> tuple:
        """Execute a command and return the output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 30 seconds"
        except Exception as e:
            return -1, "", str(e)

    def create_python_script(self, task: str) -> str:
        """Create a Python script based on the task description."""
        return self.code_generator.create_script_file(task)

    def run(self):
        """Run the task agent."""
        self.console.print(Panel.fit(
            "[bold blue]AI Task Agent[/bold blue]\n"
            "Enter your task and I'll help you execute it step by step.",
            title="Welcome",
            border_style="blue"
        ))
        
        while True:
            task = Prompt.ask("\n[bold green]Enter your task[/bold green] (or 'exit' to quit)")
            
            if task.lower() == 'exit':
                break
            
            # Generate and display the plan
            steps = self.generate_plan(task)
            
            if not steps:
                self.console.print("[red]Failed to generate a plan. Please try again.[/red]")
                continue
            
            self.console.print("\n[bold yellow]Proposed Plan:[/bold yellow]")
            for i, step in enumerate(steps, 1):
                self.console.print(f"\n[cyan]{i}. {step['description']}[/cyan]")
                if step['command']:
                    self.console.print(f"   Command: [green]{step['command']}[/green]")
            
            # Ask for confirmation
            if Prompt.ask("\n[bold yellow]Would you like to proceed with this plan?[/bold yellow]", choices=["y", "n"], default="y") == "n":
                continue
            
            # Execute each step
            for i, step in enumerate(steps, 1):
                self.console.print(f"\n[bold blue]Executing step {i}: {step['description']}[/bold blue]")
                
                if step['command']:
                    self.console.print(f"[green]Running command: {step['command']}[/green]")
                    returncode, stdout, stderr = self.execute_command(step['command'])
                    
                    if returncode == 0:
                        if stdout:
                            self.console.print("[green]Output:[/green]")
                            self.console.print(Markdown(f"```\n{stdout}\n```"))
                    else:
                        self.console.print(f"[red]Error executing command: {stderr}[/red]")
                        if Prompt.ask("\n[bold yellow]Would you like to retry this step with modifications?[/bold yellow]", choices=["y", "n"], default="n") == "n":
                            break
            
            self.console.print("\n[bold green]Task completed![/bold green]")

if __name__ == "__main__":
    agent = TaskAgent()
    agent.run() 