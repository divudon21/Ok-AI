import os
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI()

# CORS Configurations - Saari settings pehle jaisi safe hain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

class ChatRequest(BaseModel):
    message: str

# TOOL: Hardcore Terminal Execution System (Root Permission)
def run_terminal_command(command: str) -> str:
    """
    Executes any bash command inside the secure Linux sandbox workspace (/tmp).
    Use this to run python scripts, compile Flutter apps, build APKs, or manage git operations (like git worktree).
    """
    try:
        full_command = f"cd /tmp && {command}"
        env = os.environ.copy()
        
        result = subprocess.run(
            full_command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            errors="replace",
            timeout=300,
            env=env
        )
        
        output = f"Exit Code: {result.returncode}\n"
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: Command execution timed out after 5 minutes to prevent server freeze."
    except Exception as e:
        return f"SYSTEM ERROR: {str(e)}"

@app.post("/chat")
async def agent_chat(request: ChatRequest):
    user_prompt = request.message
    
    system_instruction = (
        "You are an expert AI Agent Builder operating inside a fully equipped Linux sandbox.\n\n"
        "YOUR DEVELOPMENT ENVIRONMENT capabilities:\n"
        "- **Python 3** is installed. You can write and execute python scripts (`python3 script.py`).\n"
        "- **Flutter & Dart SDK** are pre-installed globally. You can run `flutter create` and `flutter build apk --release`.\n"
        "- **Android Native Build System** is pre-installed. Full OpenJDK 17, Android SDK (API 34), Build-Tools (34.0.0), and Gradle Build Binary are ready. You can create Native Android apps (using gradle wrappers) and build them directly.\n"
        "- **HOP-AI SDK** is pre-installed. You can use 'import hop' in your python scripts to interact with remote cloud volumes, manage infrastructure, or offload long-running tasks if necessary.\n"
        "- You are operating with full administrative permissions inside the `/tmp` directory.\n\n"
        "YOUR AVAILABLE TOOLS:\n"
        "- `run_terminal_command`: Call this tool to run any shell/bash script or build commands. Do NOT wrap shell code in text-based markdown blocks if you intend to run it; execute it directly via this tool.\n"
        "- `Google Search`: You have native access to live Google Search. Use it automatically whenever you need to look up documentation for APIs (like catbox.moe, gofile.io, transfer.sh), research web endpoints, check dependency updates, or debug compilation errors.\n\n"
        "CRITICAL APPLICATION GENERATION RULES:\n"
        "- The workspace sandbox is initially empty. There are no pre-existing Android or Flutter templates inside `/tmp`. If you are tasked to create an app, you MUST programmatically write and create every single source directory, file structure, configuration script, layout resource, and source file entirely from scratch.\n"
        "- Always use standard POSIX compatible shell scripting loops (e.g., `for i in 1 2 3; do ... done`) instead of advanced bash-specific loops like `for ((i=0; i<3; i++))` because the sandbox default runtime shell executor is `/bin/sh`.\n\n"
        "ADVANCED GIT WORKSPACE MANAGEMENT:\n"
        "- You are encouraged to use `git worktree` when managing parallel tasks, feature implementations, or isolated testing branches. Instead of risky checkout switching or stashing uncommitted modifications, utilize `git worktree add -b <branch-name> <path>` to spin up isolated, standalone directories inside `/tmp` for separate branches. This keeps the main codebase safe and unpolluted during builds.\n\n"
        "CRITICAL EXECUTION RULES:\n"
        "- Analyze tool execution outputs carefully. If a command or build script fails, analyze the error log, use Google Search to find a solution or documentation if needed, self-correct, update your code, and execute again until successful.\n"
        "- Once the objective is completed successfully (e.g., app compiled or file uploaded), present a clean summary and direct download links to the user."
    )
    
    try:
        # Custom functional tools mapping
        custom_tools = {
            "run_terminal_command": run_terminal_command
        }
        
        # Grounding configs for native tool tracking
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[run_terminal_command, {'google_search': {}}],
            temperature=0.2
        )
        
        # Production ready session locked to stable gemini endpoint
        chat = client.chats.create(model='gemini-2.0-flash', config=config)
        response = chat.send_message(user_prompt)
        
        max_turns = 6 
        current_turn = 0
        execution_history = []
        
        # AGENT EXECUTION LOOP
        while response.function_calls and current_turn < max_turns:
            function_responses = []
            
            for function_call in response.function_calls:
                name = function_call.name
                args = function_call.args
                call_id = function_call.id
                
                if name in custom_tools:
                    tool_output = custom_tools[name](**args)
                    
                    execution_history.append({
                        "turn": current_turn + 1,
                        "tool_called": name,
                        "arguments": args,
                        "raw_output": tool_output
                    })
                    
                    function_responses.append(
                        types.Part.from_function_response(
                            name=name,
                            response={"result": tool_output},
                            id=call_id
                        )
                    )
            
            if function_responses:
                response = chat.send_message(function_responses)
            else:
                break
                
            current_turn += 1
            
        return {
            "agent_response": response.text,
            "execution_history": execution_history if execution_history else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
