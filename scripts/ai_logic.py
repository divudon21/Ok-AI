import os
import requests
import base64
from github import Github

# Env variables
gh_token = os.getenv('GH_TOKEN')
hf_token = os.getenv('HF_TOKEN')
issue_body = os.getenv('ISSUE_BODY')
repo_name = "divudon21/Ok-AI"

def get_ai_response(prompt):
    # Hugging Face Model (Mistral is great for instructions)
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    payload = {
        "inputs": f"<s>[INST] You are an Android expert. Based on this request: '{issue_body}', rewrite the following code completely to implement the changes. Return ONLY the code, no explanations. [/INST]</s>",
        "parameters": {"max_new_tokens": 2048}
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]['generated_text'].split("[/INST]</s>")[-1].strip()
    else:
        raise Exception(f"AI Error: {response.text}")

def main():
    g = Github(gh_token)
    repo = g.get_repo(repo_name)
    
    # Path to the main file you want the AI to edit
    # Aapki repo ke hisaab se typical Android path:
    file_path = "app/src/main/java/com/example/okai/MainActivity.kt" 

    try:
        # 1. Purana code read karna
        contents = repo.get_contents(file_path)
        old_code = contents.decoded_content.decode()

        # 2. AI se naya code mangna
        print("AI is thinking...")
        new_code = get_ai_response(old_code)

        # 3. GitHub par update karna
        if new_code and len(new_code) > 10: # Safety check
            repo.update_file(
                path=file_path,
                message=f"AI Fix: {issue_body[:50]}",
                content=new_code,
                sha=contents.sha
            )
            print("Code updated successfully!")
        else:
            print("AI returned empty or invalid code.")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
  
