# AI Task Agent

An intelligent agent that can perform local computer tasks based on natural language instructions.

## Features

- Natural language task processing
- AI-powered task planning and execution
- Interactive command-line interface
- Task validation and retry mechanism
- Safe execution with user approval

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Run the agent from the command line:
```bash
python main.py
```

Enter your task in natural language, and the agent will:
1. Generate a plan
2. Ask for your approval
3. Execute the approved tasks
4. Verify success and retry if needed

## Safety

- All tasks require explicit user approval before execution
- The agent provides detailed explanations of planned actions
- Failed tasks can be refined and retried # AI-Agent
