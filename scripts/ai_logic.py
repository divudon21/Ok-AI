import os
import requests
from github import Github

# 1. Setup Connections
gh_token = os.getenv('GH_TOKEN')
hf_token = os.getenv('HF_TOKEN')
issue_body = os.getenv('ISSUE_BODY')
repo_name = "divudon21/Ok-AI"

g = Github(gh_token)
repo = g.get_repo(repo_name)

def ask_ai(prompt):
    # Using Hugging Face Inference API
    API_URL = "https://api-inference.huggingface.co/models/bigcode/starcoder2-15b"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    # System prompt to keep AI on track
    full_prompt = f"As an Android Expert, modify the code for: {prompt}. Return only the code."
    
    response = requests.post(API_URL, headers=headers, json={"inputs": full_prompt})
    return response.json()[0]['generated_text']

def main():
    if not issue_body:
        print("No instructions found in the issue.")
        return

    print(f"AI is processing: {issue_body}")
    
    # Simple Logic: For now, it reads a target file (e.g., MainActivity.kt)
    # In advanced versions, we can let AI 'choose' the file.
    target_file = "app/src/main/java/com/example/okai/MainActivity.kt"
    
    try:
        file_content = repo.get_contents(target_file)
        old_code = file_content.decoded_content.decode()
        
        # Ask AI to modify the code
        new_code = ask_ai(f"Update this code based on these instructions: {issue_body}\n\nOld Code:\n{old_code}")

        # Update file on GitHub
        repo.update_file(
            path=target_file,
            message=f"AI Auto-fix: {issue_body[:50]}",
            content=new_code,
            sha=file_content.sha
        )
        print("Successfully updated the code!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
  
