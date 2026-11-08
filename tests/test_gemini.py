"""Run this directly: python test_gemini.py"""
import os, json
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
print(f"Key loaded: {'yes' if api_key else 'NO KEY FOUND'}")
print(f"Key prefix: {api_key[:8] if api_key else 'n/a'}")

try:
    with genai.Client(api_key=api_key) as client:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents="Say hello in one word.",
            config=types.GenerateContentConfig(temperature=0.0),
        )
    print("SUCCESS:", response.text)
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
