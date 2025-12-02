import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# 1. Initialize the client using the key from .env
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 2. Make a simple call
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Just say "Hello Agent"'
    )
    print("API Test Success:", response.text)
except Exception as e:
    print("API Test Failed:", e)