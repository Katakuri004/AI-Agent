# AI Task Agent

A Python-based AI agent that can execute tasks on your local computer by generating and executing commands based on natural language instructions.

![AI Task Agent](https://img.shields.io/badge/AI-Task%20Agent-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview

This project implements an AI agent that can understand natural language instructions and convert them into executable commands. The agent uses the Hugging Face API to generate plans and code, then executes those plans on your local machine.

## Features

- **Natural Language Understanding**: Convert plain English instructions into executable commands
- **Code Generation**: Create Python scripts based on task descriptions
- **Plan Generation**: Break down complex tasks into simple, executable steps
- **Interactive Execution**: Execute commands with user confirmation
- **Error Handling**: Robust error handling and fallback mechanisms

## Architecture

The project is structured into three main components:

1. **TaskAgent**: The main agent class that handles user interaction, plan generation, and command execution
2. **CodeGenerator**: A specialized class for generating and cleaning Python code
3. **Main Script**: The entry point that initializes and runs the agent

### Component Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  TaskAgent      │────▶│  CodeGenerator  │────▶│  Hugging Face   │
│                 │     │                 │     │     API         │
│                 │     │                 │     │                 │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         │
         ▼
┌─────────────────┐
│                 │
│  Command        │
│  Execution      │
│                 │
└─────────────────┘
```

## Code Walkthrough

### 1. TaskAgent Class

The `TaskAgent` class is the core of the application. It handles:

- **API Communication**: Sends requests to the Hugging Face API
- **Plan Generation**: Converts tasks into executable plans
- **Command Execution**: Runs commands and captures their output
- **User Interaction**: Provides a console interface for users

#### Key Methods:

- `__init__`: Initializes the agent with API credentials
- `generate_plan`: Creates a step-by-step plan for executing a task
- `execute_command`: Runs a command and returns its output
- `run`: The main loop that handles user interaction

### 2. CodeGenerator Class

The `CodeGenerator` class is responsible for:

- **Code Generation**: Creating Python scripts based on task descriptions
- **Code Cleaning**: Removing markdown, language tags, and fixing indentation
- **Code Validation**: Ensuring the generated code is valid Python
- **Fallback Mechanisms**: Providing fallback code when generation fails

#### Key Methods:

- `clean_code`: Removes markdown and formatting artifacts from generated code
- `generate_code`: Sends a request to the API to generate Python code
- `_is_valid_python`: Checks if the generated code looks like valid Python
- `_get_fallback_code`: Provides fallback code based on the task description
- `create_script_file`: Generates code and saves it to a file

### 3. Main Script

The `main.py` file serves as the entry point for the application. It:

- Loads environment variables
- Creates an instance of the TaskAgent
- Runs the agent's main loop

## Code Concepts Explained

### 1. Natural Language Processing

The agent uses the Hugging Face API to process natural language instructions. The API is a large language model that can understand and generate text based on prompts.

```python
prompt = f"""<s>[INST] Create a step-by-step plan to execute this task: {task}

For each step, provide:
1. A clear description of what needs to be done
2. The exact command to execute (if applicable)

Example format:
1. Step description: Create a Python script
   Command: python script.py

2. Step description: Run the script
   Command: python script.py

Keep the plan simple and focused on the task. [/INST]</s>"""
```

This prompt instructs the model to generate a plan with specific formatting, making it easier to parse the response.

### 2. Code Generation and Cleaning

The code generation process involves several steps:

1. **Prompt Creation**: Creating a prompt that instructs the model to generate Python code
2. **API Request**: Sending the prompt to the Hugging Face API
3. **Response Processing**: Extracting the generated code from the API response
4. **Code Cleaning**: Removing markdown, language tags, and fixing indentation
5. **Code Validation**: Ensuring the generated code is valid Python
6. **Fallback Mechanism**: Using fallback code if generation fails

The code cleaning process is particularly important, as it ensures that the generated code is properly formatted and can be executed without errors.

```python
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
    
    # ... more cleaning steps ...
    
    # Fix indentation with a more robust approach
    lines = []
    indent_level = 0
    in_function = False
    in_docstring = False
    
    for line in code.split('\n'):
        # ... indentation handling ...
    
    return '\n'.join(lines)
```

### 3. Indentation Handling

One of the most challenging aspects of code generation is handling indentation correctly. The `clean_code` method uses a sophisticated approach to ensure proper indentation:

- It tracks whether it's inside a function, docstring, or control structure
- It adjusts the indentation level based on the type of line
- It preserves empty lines and handles special cases like docstrings

```python
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
```

### 4. Code Validation

The agent includes a validation mechanism to ensure that the generated code is valid Python:

```python
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
```

This method checks for:
- Python keywords to ensure the code contains Python-specific syntax
- Non-Python patterns to detect if the model generated code in another language
- Proper indentation to ensure the code is formatted correctly

### 5. Fallback Mechanisms

The agent includes robust fallback mechanisms to handle cases where code generation fails:

```python
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
    
    # ... more fallback cases ...
```

This method analyzes the task description to determine what kind of fallback code to generate, ensuring that even if the API fails, the agent can still produce useful results.

### 6. Command Execution

The agent executes commands using Python's `subprocess` module:

```python
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
```

This method:
- Runs the command in a shell
- Captures both standard output and standard error
- Sets a timeout to prevent hanging
- Returns the return code, standard output, and standard error

## Usage Examples

### Example 1: Creating a Python Script

```
Enter your task: create a file called "test1.py" and inside write code to print digits 0 to 10
```

The agent will:
1. Generate a plan for creating and running the Python script
2. Create the script with code to print digits 0 to 10
3. Display the contents of the script
4. Run the script to show the output

### Example 2: Creating a Grid

```
Enter your task: create a simple code to produce 4*4 grid using "*" in a file called "test_gen.py" and execute it
```

The agent will:
1. Generate a plan for creating and running the Python script
2. Create the script with code to print a 4x4 grid of asterisks
3. Display the contents of the script
4. Run the script to show the grid

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-task-agent.git
   cd ai-task-agent
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your Hugging Face API key:
   ```
   HUGGINGFACE_API_KEY=your_api_key_here
   ```

4. Run the agent:
   ```
   python main.py
   ```

## Requirements

- Python 3.8 or higher
- `requests` library for API communication
- `rich` library for console formatting
- `python-dotenv` for environment variable management
- Hugging Face API key

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Hugging Face for providing the API
- The Python community for the excellent libraries used in this project
