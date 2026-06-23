from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

def test_api():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hola, prueba de conexion"
        )
        print("SUCCESS")
        print(response.text)
    except Exception as e:
        print("FAILURE")
        print(str(e))

if __name__ == "__main__":
    test_api()
