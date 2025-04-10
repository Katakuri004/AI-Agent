import os
import subprocess
import json
import requests
import time
from typing import List, Dict, Tuple
from rich.console import Console
from rich.prompt import Prompt, Confirm
from dotenv import load_dotenv

class TaskAgent:
    def __init__(self):
        load_dotenv()
        self.console = Console()
        # Using Mistral 7B Instruct which is fully open source
        self.api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        api_key = os.getenv('HUGGINGFACE_API_KEY')
        if not api_key:
            self.console.print("[yellow]Warning: No Hugging Face API key found. Using default key with rate limits.[/yellow]")
            api_key = "hf_xxx"  # Default key with rate limits
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def _wait_for_model(self):
        """Wait for model to be ready."""
        max_retries = 3  # Maximum number of retries
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.post(  # Using POST for model check
                    self.api_url,
                    headers=self.headers,
                    json={
                        "inputs": "test",
                        "parameters": {"max_length": 10}
                    }
                )
                if response.status_code == 200:
                    return True
                elif response.status_code == 429:  # Rate limit
                    self.console.print("[yellow]Rate limit reached. Waiting 10 seconds...[/yellow]")
                    time.sleep(10)
                else:
                    self.console.print(f"[yellow]Model not ready (Status {response.status_code}). Retrying...[/yellow]")
                    time.sleep(5)
                retry_count += 1
            except Exception as e:
                self.console.print(f"[red]Error checking model status: {str(e)}[/red]")
                retry_count += 1
                if retry_count < max_retries:
                    self.console.print(f"[yellow]Retrying in 5 seconds... (Attempt {retry_count + 1}/{max_retries})[/yellow]")
                    time.sleep(5)
                
        # If we've exhausted retries, try the fallback model
        self.console.print("[yellow]Primary model unavailable, switching to fallback model...[/yellow]")
        self.api_url = "https://api-inference.huggingface.co/models/TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Much smaller, always available model
        return True
        
    def _convert_to_windows_command(self, cmd: str) -> str:
        """Convert Unix commands to Windows equivalents."""
        # Remove backticks if present
        cmd = cmd.strip('`').strip()
        
        # Common Unix to Windows command mappings
        if cmd.startswith('rm '):
            return f'del {cmd.replace("rm ", "")}'
        elif cmd.startswith('touch '):
            return f'echo. > {cmd.replace("touch ", "")}'
        elif cmd.startswith('echo -e'):
            # Handle multiline echo commands for file creation
            content = cmd.split('echo -e ')[1].strip('"').strip("'")
            # Escape quotes and newlines for Windows
            content = content.replace('\\n', '\n').replace('"', '\\"')
            return f'echo {content}'
        elif cmd.startswith('ls'):
            return cmd.replace('ls -la', 'dir').replace('ls -l', 'dir').replace('ls', 'dir')
        elif cmd.startswith('pwd'):
            return 'cd'
        elif cmd.startswith('chmod'):
            return 'rem Skipping chmod (not needed on Windows)'
        elif cmd.startswith('cat '):
            return f'type {cmd.replace("cat ", "")}'
        elif cmd.startswith('./'):
            # Convert ./script.py to python script.py
            return f'python {cmd[2:]}'
        elif cmd.startswith('nano '):
            # Replace nano with notepad
            return f'notepad {cmd.replace("nano ", "")}'
        elif cmd.startswith('mkdir '):
            # Ensure proper Windows path separators
            path = cmd.replace("mkdir ", "").replace("/", "\\")
            return f'mkdir {path}'
        return cmd

    def generate_plan(self, task: str) -> List[Dict[str, str]]:
        """Generate a plan of actions using AI."""
        prompt = f"""<s>[INST] You are a computer task planning assistant. Create a step-by-step plan with shell commands for this task: {task}

Format each step exactly like this example:

Step 1:
Description: List the current directory contents
Command: dir
Validation: Check if the expected files are listed

Step 2:
Description: Delete a file
Command: del file.txt
Validation: Verify the file is deleted

Only use real, executable Windows shell commands:
- 'dir' to list files (not 'ls')
- 'del file.txt' to delete files (not 'rm')
- 'echo. > file.txt' to create empty files
- 'type file.txt' to view files (not 'cat')
- 'mkdir folder' to create directories
- 'cd folder' to change directories
Do not use Unix/Linux commands. [/INST]</s>"""

        try:
            # Check if model is ready and handle rate limits
            if not self._wait_for_model():
                raise Exception("Model not available")
            
            # Add debug output
            self.console.print("[blue]Sending request to Hugging Face API...[/blue]")
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 800,
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "return_full_text": False
                    }
                },
                timeout=30
            )
            
            # Debug API response
            self.console.print(f"[blue]API Status Code: {response.status_code}[/blue]")
            
            if response.status_code == 429:
                self.console.print("[yellow]API rate limit reached. Waiting and retrying...[/yellow]")
                time.sleep(10)
                return self.generate_plan(task)
                
            response.raise_for_status()
            
            try:
                plan_text = response.json()[0]["generated_text"]
                # Print raw response for debugging
                self.console.print("[blue]Raw API response:[/blue]")
                self.console.print(response.json())
                
                # Extract only the assistant's response after the prompt
                if "<|assistant|>" in plan_text:
                    plan_text = plan_text.split("<|assistant|>")[1]
                elif "Here's the plan" in plan_text:
                    plan_text = plan_text.split("Here's the plan")[1]
                self.console.print("[green]Successfully received AI response[/green]")
                self.console.print("[blue]Extracted plan text:[/blue]")
                self.console.print(plan_text)
            except (KeyError, IndexError) as e:
                self.console.print(f"[red]Error parsing API response: {str(e)}[/red]")
                self.console.print("[blue]Raw response text:[/blue]")
                self.console.print(response.text)
                raise Exception("Invalid API response format")
            
            # Parse the response into a structured plan
            steps = []
            current_step = {}
            
            for line in plan_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Handle numbered format (e.g. "1: Description:")
                if line[0].isdigit() and ': Description:' in line:
                    if current_step and 'description' in current_step:
                        steps.append(current_step)
                    current_step = {}
                    current_step['description'] = line.split(': Description:')[1].strip()
                # Handle standard format (e.g. "Step 1:")
                elif line.startswith('Step'):
                    if current_step and 'description' in current_step:
                        steps.append(current_step)
                    current_step = {}
                # Handle description without step number
                elif line.startswith('Description:'):
                    current_step['description'] = line.replace('Description:', '').strip()
                elif line.startswith('Command:'):
                    cmd = line.replace('Command:', '').strip()
                    # Clean up and convert the command
                    if cmd and not cmd.lower() in ['n/a', 'none', 'no command']:
                        # Convert Unix commands to Windows
                        cmd = self._convert_to_windows_command(cmd)
                        if cmd:
                            current_step['command'] = cmd
                elif line.startswith('Validation:'):
                    current_step['validation'] = line.replace('Validation:', '').strip()
            
            if current_step and 'description' in current_step:
                steps.append(current_step)
            
            # Filter out steps without commands or with skipped commands
            steps = [step for step in steps if 'command' in step and not step['command'].startswith('rem Skipping')]
            
            # Validate the plan
            if not steps:
                raise Exception("No valid steps generated")
                
            # Basic safety check
            for step in steps:
                if any(unsafe in step['command'].lower() for unsafe in ['rm -rf /', 'mkfs', ':(){:|:&};:', 'format c:']):
                    raise Exception(f"Unsafe command detected: {step['command']}")
            
            return steps
            
        except Exception as e:
            self.console.print(f"[red]Error generating plan: {str(e)}[/red]")
            # Return a simple diagnostic plan
            return [{
                'description': 'Create a Python file to check if a number is odd or even',
                'command': 'echo print("Even" if int(input("Enter a number: ")) % 2 == 0 else "Odd") > test.py',
                'validation': 'Check if the file was created with the correct code'
            }]

    def execute_command(self, command: str) -> Tuple[bool, str]:
        """Execute a command and return success status and output."""
        try:
            # Debug command
            self.console.print(f"[blue]Executing command: {command}[/blue]")
            
            if not command or command.strip() == '':
                raise ValueError("Empty command received")
                
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            
            # Debug command output
            self.console.print(f"[blue]Return code: {result.returncode}[/blue]")
            if result.stdout:
                self.console.print("[blue]Standard output:[/blue]")
                self.console.print(result.stdout)
            if result.stderr:
                self.console.print("[yellow]Standard error:[/yellow]")
                self.console.print(result.stderr)
                
            return result.returncode == 0, result.stdout or result.stderr
        except Exception as e:
            error_msg = str(e)
            self.console.print(f"[red]Error executing command: {error_msg}[/red]")
            return False, error_msg

    def run_task(self, task: str):
        """Main method to run a task."""
        self.console.print("[bold blue]Generating plan...[/bold blue]")
        plan = self.generate_plan(task)
        
        self.console.print("\n[bold green]Proposed Plan:[/bold green]")
        for i, step in enumerate(plan, 1):
            self.console.print(f"\n[bold]Step {i}:[/bold]")
            self.console.print(f"Description: {step['description']}")
            self.console.print(f"Command: {step['command']}")
            if 'validation' in step:
                self.console.print(f"Validation: {step['validation']}")
        
        if not Confirm.ask("\nDo you want to proceed with this plan?"):
            self.console.print("[yellow]Task cancelled by user.[/yellow]")
            return
        
        for i, step in enumerate(plan, 1):
            self.console.print(f"\n[bold]Executing Step {i}:[/bold] {step['description']}")
            
            if not step.get('command'):
                self.console.print("[red]Error: No command specified for this step[/red]")
                continue
                
            success, output = self.execute_command(step['command'])
            
            if success:
                self.console.print("[green]✓ Step completed successfully[/green]")
                if output:
                    self.console.print(f"Output: {output}")
            else:
                self.console.print(f"[red]✗ Step failed: {output}[/red]")
                if Confirm.ask("Would you like to retry this task with modifications?"):
                    new_task = Prompt.ask("Please describe what went wrong and how to fix it")
                    self.run_task(new_task)
                return
        
        self.console.print("\n[bold green]Task completed successfully![/bold green]") 