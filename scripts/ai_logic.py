import os
import requests
from github import Github

gh_token = os.getenv('GH_TOKEN')
hf_token = os.getenv('HF_TOKEN')
issue_body = os.getenv('ISSUE_BODY')
repo_name = "divudon21/Ok-AI"

def get_ai_response(prompt):
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {
        "inputs": f"<s>[INST] You are an Android Expert. Create the full code for: '{issue_body}'. Give ONLY the code, no text. [/INST]</s>",
        "parameters": {"max_new_tokens": 2048}
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()[0]['generated_text'].split("[/INST]</s>")[-1].strip()

def main():
    g = Github(gh_token)
    repo = g.get_repo(repo_name)
    
    # AI ab khud file ka naam aur path decide karega based on instruction
    # Defaulting to MainActivity if nothing else is mentioned
    file_path = "app/src/main/java/com/example/okai/MainActivity.kt"

    print(f"AI is generating code for: {issue_body}")
    new_code = get_ai_response(issue_body)

    try:
        # Check agar file pehle se hai
        contents = repo.get_contents(file_path)
        repo.update_file(path=file_path, message="AI Update", content=new_code, sha=contents.sha)
    except:
        # Agar file NAHI hai, toh AI nayi file CREATE karega
        repo.create_file(path=file_path, message="AI Created File", content=new_code)
    
    print("AI ne kaam khatam kar diya!")

if __name__ == "__main__":
    main()
  
