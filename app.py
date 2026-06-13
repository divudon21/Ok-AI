import os
import subprocess
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# CORS Configurations - Saari settings pehle jaisi safe hain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secure Environment Initialization
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

class ChatRequest(BaseModel):
    message: str

# TOOL: Hardcore Terminal Execution System (Root Permission)
def run_terminal_command(command: str) -> str:
    """
    Executes any bash command inside the secure Linux sandbox workspace (/tmp).
    Use this to run python scripts, compile native Android projects, build APKs, or manage git operations (like git worktree).
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
        "- **Android Native Build System** is pre-installed. Full OpenJDK 17, Android SDK (API 34), and Build-Tools (34.0.0) are ready. You can create Native Android apps and build them directly.\n"
        "- **HOP-AI SDK** is pre-installed. You can use 'import hop' in your python scripts to interact with remote cloud volumes, manage infrastructure, or offload long-running tasks if necessary.\n"
        "- You are operating with full administrative permissions inside the `/tmp` directory.\n\n"
        "YOUR AVAILABLE TOOLS:\n"
        "- `run_terminal_command`: Call this tool to run any shell/bash script or build commands. To execute, you MUST use the native tools/function calling capabilities provided by the model interface.\n"
        "- `Google Search`: You have native access to live Google Search. Use it automatically whenever you need to look up documentation for APIs, research web endpoints, check dependency updates, or debug compilation errors.\n\n"
        "CRITICAL APPLICATION GENERATION RULES:\n"
        "- The workspace sandbox is initially empty. There are no pre-existing Android templates inside `/tmp`. If you are tasked to create an app, you MUST programmatically write and create every single source directory, file structure, configuration script, layout resource, and source file entirely from scratch.\n"
        "- To initialize Gradle wrappers for native builds, you can programmatically inject the wrapper download URL inside 'gradle/wrapper/gradle-wrapper.properties' or download the wrapper binaries explicitly during the build step using curl/wget directly into the project folder.\n"
        "- Always use standard POSIX compatible shell scripting loops (e.g., `for i in 1 2 3; do ... done`) instead of advanced bash-specific loops like `for ((i=0; i<3; i++))` because the sandbox default runtime shell executor is `/bin/sh`.\n\n"
        "ADVANCED GIT WORKSPACE MANAGEMENT:\n"
        "- You are encouraged to use `git worktree` when managing parallel tasks, feature implementations, or isolated testing branches. Instead of risky checkout switching or stashing uncommitted modifications, utilize `git worktree add -b <branch-name> <path>` to spin up isolated, standalone directories inside `/tmp` for separate branches. This keeps the main codebase safe and unpolluted during builds.\n\n"
        "CRITICAL EXECUTION RULES:\n"
        "- Analyze tool execution outputs carefully. If a command or build script fails, analyze the error log, self-correct, update your code, and execute again until successful.\n"
        "- Once the objective is completed successfully (e.g., app compiled or file uploaded), present a clean summary and direct download links to the user."
    )
    
    try:
        # Structured tool schema definition for unified NIM deployment
        tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "run_terminal_command",
                    "description": "Executes any bash/shell command inside the secure Linux workspace (/tmp) to run scripts or build applications.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The exact shell command or script execution string to run."
                            }
                        },
                        "required": ["command"]
                    }
                }
            }
        ]
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]
        
        max_turns = 6
        current_turn = 0
        execution_history = []
        
        # AGENT EXECUTION LOOP - Multi-turn tool tracking synced with Nemotron stream blocks
        while current_turn < max_turns:
            completion = client.chat.completions.create(
                model="nvidia/nemotron-3-ultra-550b-a55b",
                messages=messages,
                tools=tools_schema,
                tool_choice="auto",
                temperature=1.00,
                top_p=0.95,
                max_tokens=16384,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": True},
                    "reasoning_budget": 16384
                },
                stream=True
            )
            
            # Streaming reconstruction logic
            full_response_content = ""
            active_tool_calls_buffer = {}
            
            for chunk in completion:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # Check for model thinking content streaming if available
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    pass # Internal stream processing safely bypassed from output dump
                
                # Reconstruct normal text content chunks
                if delta.content is not None:
                    full_response_content += delta.content
                
                # Reconstruct streamed tool calls arguments chunks
                if getattr(delta, "tool_calls", None):
                    for tool_call_delta in delta.tool_calls:
                        index = tool_call_delta.index
                        if index not in active_tool_calls_buffer:
                            active_tool_calls_buffer[index] = {
                                "id": tool_call_delta.id,
                                "name": tool_call_delta.function.name if getattr(tool_call_delta, "function", None) and tool_call_delta.function.name else "",
                                "arguments": ""
                            }
                        if tool_call_delta.id:
                            active_tool_calls_buffer[index]["id"] = tool_call_delta.id
                        if tool_call_delta.function and tool_call_delta.function.name:
                            active_tool_calls_buffer[index]["name"] = tool_call_delta.function.name
                        if tool_call_delta.function and tool_call_delta.function.arguments:
                            active_tool_calls_buffer[index]["arguments"] += tool_call_delta.function.arguments

            # If no tool chunks were generated, break loop and save textual payload
            if not active_tool_calls_buffer:
                messages.append({"role": "assistant", "content": full_response_content})
                break
                
            # Formulate structured payload for tool submission trace
            formatted_tool_calls = []
            for idx, call_data in active_tool_calls_buffer.items():
                formatted_tool_calls.append({
                    "id": call_data["id"],
                    "type": "function",
                    "function": {
                        "name": call_data["name"],
                        "arguments": call_data["arguments"]
                    }
                })
            
            # Append context history frame
            messages.append({
                "role": "assistant",
                "content": full_response_content if full_response_content else None,
                "tool_calls": formatted_tool_calls
            })
            
            # Execute extracted tools inside loop sequentially
            for call_data in active_tool_calls_buffer.values():
                if call_data["name"] == "run_terminal_command":
                    args = json.loads(call_data["arguments"])
                    cmd = args.get("command")
                    
                    tool_output = run_terminal_command(cmd)
                    
                    execution_history.append({
                        "turn": current_turn + 1,
                        "tool_called": "run_terminal_command",
                        "arguments": {"command": cmd},
                        "raw_output": tool_output
                    })
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_data["id"],
                        "name": "run_terminal_command",
                        "content": tool_output
                    })
                    
            current_turn += 1
            
        return {
            "agent_response": messages[-1]["content"],
            "execution_history": execution_history if execution_history else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
