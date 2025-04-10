import os
from dotenv import load_dotenv
from agent import TaskAgent

def main():
    # Load environment variables
    load_dotenv()
    
    # Create and run the agent
    agent = TaskAgent()
    agent.run()

if __name__ == "__main__":
    main() 