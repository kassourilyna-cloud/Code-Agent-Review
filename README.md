# Code-Agent-Review
This is a Python-based command-line tool that acts as an intelligent code reviewer for full files. It automatically runs local code scanners, passes the code to Google's Gemini model for a deeper security review, prints a clean report table, and opens a live chat so you can ask the agent questions or request code fixes.
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

## Sample Code
<img width="1366" height="683" alt="table_messy_code_1" src="https://github.com/user-attachments/assets/4cc8a58b-ab1f-4e59-a81c-13b9b476a957" />

<img width="1366" height="732" alt="table_messy_code_2" src="https://github.com/user-attachments/assets/00a01308-25ea-43aa-ae3b-386f040fc519" />

## challenges you ran into:
1. **Switching from Ollama to Gemini API**: 
   * *The Problem*: I originally wanted to build this agent using a completely local model running on my computer via Ollama . However, I ran into two major roadblocks: local models require massive computer hardware resources (GPU/RAM) to process files smoothly, and smaller local models frequently struggle with reliable multi-step tool use (function calling). The local model would often hallucinate tool arguments or fail to realize it needed to run a web search.
   * *The fix*:use the Google GenAI SDK (`Gemini`). Cloud models have much stronger reasoning capabilities, handle tool call parameters perfectly, and don't slow down my local system's performance.
2. **Managing Free-Tier API Limits**: Having the AI run its own tools back and forth used up the free 20-requests-per-day limit almost instantly. I solved this by changing the code to run Ruff and Bandit locally on my computer first, then passing those logs to Gemini all at once. This reduced the API calls to just 2 requests per run, letting me test the agent much longer.
3. **Fixing the Chat Memory Bug**: When adding the chat feature, a bug appeared where the AI would get confused and only show one bug instead of all of them. This happened because the command forcing the AI to format the final table leaked into the chat's active memory history. I fixed this by copying the chat history snapshot cleanly before formatting the table, keeping the live chat session separate and smart.
   
## future improvements :
If I had more time :
* I would build a file-patching feature. This would allow the agent to automatically modify and rewrite the secure code fixes directly back into the script on your computer after you approve the suggestion in the chat. and improve the chat bar better (Fix for Context Length Truncation  and more fixes for sure) ,
* Reviewing Whole Folders ,
* Specialist Sub-Agents by multiple smaller agents in parallel—one focusing only on performance, one only on security, and one final "Coordinator" agent to clean up their notes and draw the final table.





