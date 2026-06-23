import openai
import os
from dotenv import load_dotenv

load_dotenv()

def test_kimi():
    api_key = os.getenv("KIMI_API_KEY")
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.cn/v1"
    )
    try:
        # Intentar listar modelos para ver cuáles tiene acceso
        print("Intentando listar modelos de Moonshot...")
        models = client.models.list()
        for m in models:
            print(f"- {m.id}")
            
        print("\nPrueba de chat...")
        response = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[{"role": "user", "content": "Hola"}]
        )
        print("Respuesta:", response.choices[0].message.content)
    except Exception as e:
        print(f"Error en Kimi: {e}")

if __name__ == "__main__":
    test_kimi()
