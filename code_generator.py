import requests
import os
from rich.console import Console

console = Console()

class CodeGenerator:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.console = Console()

    def clean_code(self, code: str) -> str:
        """Clean up generated code by removing markdown and formatting artifacts."""
        # Remove language tags and markdown
        code = code.replace(':python', '').replace('python', '')
        code = code.strip('`')
        
        # Remove code block markers
        if "```" in code:
            parts = code.split("```")
            for part in parts:
                clean = part.strip()
                if clean and not clean.lower().startswith(('python', 'py', ':')):
                    code = clean
                    break
        
        # Remove triple quotes
        if code.count("'''") % 2 != 0:
            code = code.replace("'''", '')
        if code.count('"""') % 2 != 0:
            code = code.replace('"""', '')
        
        # Remove escaped characters
        code = code.replace('\\_', '_')
        code = code.replace('\\n', '\n')
        code = code.replace('\\\\', '\\')
        code = code.replace('\\t', '    ')  # Replace tabs with spaces
        
        # Fix indentation with a more robust approach
        lines = []
        indent_level = 0
        in_function = False
        in_docstring = False
        
        for line in code.split('\n'):
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                lines.append('')
                continue
                
            # Handle docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                    if in_function:
                        lines.append('    ' * indent_level + stripped)
                    else:
                        lines.append(stripped)
                else:
                    in_docstring = False
                    if in_function:
                        lines.append('    ' * indent_level + stripped)
                    else:
                        lines.append(stripped)
                continue
                
            # Skip lines inside docstrings
            if in_docstring:
                if in_function:
                    lines.append('    ' * indent_level + stripped)
                else:
                    lines.append(stripped)
                continue
                
            # Handle function definitions
            if stripped.startswith('def '):
                in_function = True
                indent_level = 0
                lines.append(stripped)
                continue
                
            # Handle main block
            if stripped == 'if __name__ == "__main__":' or stripped == "if __name__ == '__main__':":
                in_function = False
                indent_level = 0
                lines.append(stripped)
                continue
                
            # Handle control structures
            if stripped.startswith(('if ', 'for ', 'while ', 'try:', 'except ', 'else:', 'elif ')):
                if in_function:
                    lines.append('    ' * indent_level + stripped)
                    if stripped.endswith(':'):
                        indent_level += 1
                else:
                    lines.append(stripped)
                    if stripped.endswith(':'):
                        indent_level += 1
                continue
                
            # Handle return statements
            if stripped.startswith('return '):
                if in_function:
                    lines.append('    ' * indent_level + stripped)
                else:
                    lines.append(stripped)
                continue
                
            # Handle print statements
            if stripped.startswith('print('):
                if in_function:
                    lines.append('    ' * indent_level + stripped)
                else:
                    lines.append(stripped)
                continue
                
            # Handle comments
            if stripped.startswith('#'):
                if in_function:
                    lines.append('    ' * indent_level + stripped)
                else:
                    lines.append(stripped)
                continue
                
            # Handle all other lines
            if in_function:
                lines.append('    ' * indent_level + stripped)
            else:
                lines.append(stripped)
        
        return '\n'.join(lines)

    def generate_code(self, task: str) -> str:
        """Generate a Python script based on the task description."""
        prompt = f"""<s>[INST] Write a Python script for this task: {task}

IMPORTANT: You must write ONLY Python code. Do not write HTML, CSS, JavaScript, or any other language.
The code must be valid Python that can be executed directly.

Example of valid Python code:
def print_numbers():
    for i in range(10):
        print(i)

if __name__ == '__main__':
    print_numbers()

Write ONLY the Python code, no language tags or markdown. Use 4 spaces for indentation. [/INST]</s>"""

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
            code = response.json()[0]["generated_text"].strip()
            
            # Clean up the code
            clean_code = self.clean_code(code)
            
            # Validate that this is actually Python code
            if not self._is_valid_python(clean_code):
                self.console.print("[yellow]Generated code doesn't look like Python. Using fallback code.[/yellow]")
                return self._get_fallback_code(task)
            
            return clean_code
            
        except Exception as e:
            self.console.print(f"[red]Error generating Python script: {str(e)}[/red]")
            return self._get_fallback_code(task)
    
    def _is_valid_python(self, code: str) -> bool:
        """Check if the code looks like valid Python."""
        # Check for common Python keywords
        python_keywords = ['def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ', 'return ', 'print(']
        has_python_keywords = any(keyword in code for keyword in python_keywords)
        
        # Check for common non-Python patterns
        non_python_patterns = ['<html', '<body', '<div', '{', '}', ';', 'function', 'var ', 'let ', 'const ']
        has_non_python = any(pattern in code for pattern in non_python_patterns)
        
        # Check for proper Python indentation
        lines = code.split('\n')
        has_indentation = any(line.startswith('    ') for line in lines)
        
        return has_python_keywords and not has_non_python and has_indentation
    
    def _get_fallback_code(self, task: str) -> str:
        """Generate a simple fallback Python script based on the task."""
        # Extract key information from the task
        task_lower = task.lower()
        
        # Check for common patterns in the task
        if 'print' in task_lower and ('number' in task_lower or 'digit' in task_lower):
            if '0' in task_lower and '10' in task_lower:
                return """def print_numbers():
    # Print numbers from 0 to 10
    for i in range(11):
        print(i)

if __name__ == '__main__':
    print_numbers()"""
            else:
                return """def print_numbers():
    # Print numbers from 1 to 10
    for i in range(1, 11):
        print(i)

if __name__ == '__main__':
    print_numbers()"""
        
        elif 'grid' in task_lower and ('*' in task_lower or 'asterisk' in task_lower):
            return """def print_grid(size=4):
    # Print a grid of asterisks
    for i in range(size):
        print('* ' * size)

if __name__ == '__main__':
    print_grid()"""
        
        elif 'hello' in task_lower or 'greet' in task_lower:
            return """def greet():
    # Print a greeting message
    print("Hello, World!")

if __name__ == '__main__':
    greet()"""
        
        else:
            # Default fallback
            return """def main():
    # This is a simple Python script
    print("Hello, World!")
    print("This script was generated automatically.")

if __name__ == '__main__':
    main()"""

    def create_script_file(self, task: str, filename: str = None) -> str:
        """Generate a Python script and save it to a file."""
        # Extract filename from task if not provided
        if filename is None:
            import re
            match = re.search(r'in a file called ["\']?([^"\']+)["\']?', task)
            if match:
                filename = match.group(1)
            else:
                filename = "script.py"
        
        # Generate the code
        code = self.generate_code(task)
        
        # Save to file
        with open(filename, 'w', newline='\n') as f:
            f.write(code)
        
        return filename 