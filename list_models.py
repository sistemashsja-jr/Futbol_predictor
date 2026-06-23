from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

def list_mods():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    try:
        print("Modelos disponibles:")
        for m in client.models.list():
            print(f"- {m.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_mods()
