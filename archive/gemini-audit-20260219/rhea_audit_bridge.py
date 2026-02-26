import google.generativeai as genai
import os
import subprocess

# Configure the Engine
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-pro') # Or gemini-2.0-flash-thinking

def get_git_state():
    # Extracts the "Active Logic" from the current branch
    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
    diff = subprocess.check_output(["git", "diff", "main"]).decode()
    return branch, diff

branch_name, logic_delta = get_git_state()

prompt = f"""
ACT AS: Lead Systems Architect.
TASK: Perform a Lossless Audit of the following Rhea Project logic delta.
BRANCH: {branch_name}
DELTA DATA: 
{logic_delta}

AUDIT CRITERIA:
1. Identify any 'Semantic Drift' from the Main branch.
2. Check for 'Axiomatic Consistency' (Do the new scripts break established rules?).
3. Output a 'Verification & Validation' report in Markdown.
"""

response = model.generate_content(prompt)
print(response.text)
