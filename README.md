# Code-Agent-Review
This is a Python-based command-line tool that acts as an intelligent code reviewer. It automatically runs local code scanners, passes the code to Google's Gemini model for a deeper security review, prints a clean report table, and opens a live chat so you can ask the agent questions or request code fixes.
##  What Was Built and How It Works

This project is built as an **intelligent workflow** that combines traditional local code tools with an advanced AI model. Instead of making the AI look for everything from scratch, the system breaks the review process into distinct, clean steps:

1. **Local Pre-Scanning**: The tool runs two popular Python scanners locally on your machine: `Ruff` (to look for code style errors) and `Bandit` (to find common security risks). 
2. **AI Analysis**: The tool reads your code file along with the logs from Ruff and Bandit, and sends them to Gemini. If Gemini spots a specific bug mention or security vulnerability , it automatically triggers a web search tool to look up live information about how that vulnerability works.
3. **Report Generation**: The script securely copies the conversation summary and organizes the findings into a strict JSON format. It then uses the `rich` library to draw a beautifully formatted table in your terminal showing the exact location, severity, and explanation of every bug.
4. **Interactive Chat Room**: Instead of closing right after printing the table, the script keeps the terminal session open. You can type questions directly to the agent (e.g., *"How do I fix line 18?"*), and it will reply instantly with full memory of the code it just reviewed.

## Tools and Libraries Used

* **Python**: The core language used to write the script.
* **google-genai SDK**: The official Google library used to connect to and communicate with the Gemini AI models (`gemini-2.5-flash-lite` or `gemini-2.5-flash`).
* **Ruff & Bandit**: Local terminal tools used to scan code files for syntax issues and basic security flaws before using the AI.
* **Rich**: A Python package used to display beautiful text, loading spinners, and colored tables directly inside the command prompt.

##  How to Run and Use It

1. Open your terminal in your project directory:
   ```cmd
   cd "C:\Users\ZED\Desktop\Code Review Agent"
   
2. Set your Gemini API key in your terminal environment:
  ```cmd
   set GEMINI_API_KEY=your_actual_api_key_here
  ```

3. Run the agent by passing the path of the Python file you want to review:
 ```cmd
  python agent.py messy_code.py
 ```

##Sample Code Review

##Challenges Faced & Things to Improve


