import os
import requests
from github import Github

# Setup
gh_token = os.getenv('GH_TOKEN')
hf_token = os.getenv('HF_TOKEN')
issue_body = os.getenv('ISSUE_BODY')
repo_name = "divudon21/Ok-AI"

def main():
    if not issue_body:
        print("Issue body empty!")
        return

    g = Github(gh_token)
    repo = g.get_repo(repo_name)

    # AI ko instruction dena
    # Hum Hugging Face ki Mistral ya StarCoder model use kar sakte hain
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    prompt = f"Target: Android App. Task: {issue_body}. Provide only the code changes."
    
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    
    # Note: As an expert, I suggest starting with a specific file 
    # to avoid the AI getting confused.
    target_path = "app/src/main/java/com/example/okai/MainActivity.kt" 
    
    try:
        contents = repo.get_contents(target_path)
        # Yahan AI ka generated code update hoga
        # Simple test: Hum abhi sirf verify kar rahe hain ki flow kaam kar raha hai
        print(f"AI is working on: {issue_body}")
        
        # Ye part AI ke response ko file mein write karega
        # (Real implementation needs response parsing)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
  
