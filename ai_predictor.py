from google import genai
import os
from dotenv import load_dotenv
import openai
import anthropic
import requests
from stats_engine import StatsEngine
try:
    from groq import Groq
except ImportError:
    Groq = None
try:
    from mistralai import Mistral
except ImportError:
    Mistral = None

load_dotenv()

class AIPredictor:
    def __init__(self):
        # Gemini
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_client = genai.Client(api_key=self.gemini_key) if self.gemini_key else None
        
        # Groq
        self.groq_key = os.getenv("GROQ_API_KEY")
        if self.groq_key and "your_groq" not in self.groq_key:
            self.groq_client = Groq(api_key=self.groq_key) if Groq else None
        else:
            self.groq_client = None

        # Mistral
        self.mistral_key = os.getenv("MISTRAL_API_KEY")
        if self.mistral_key and "your_mistral" not in self.mistral_key:
            self.mistral_client = Mistral(api_key=self.mistral_key) if Mistral else None
        else:
            self.mistral_client = None

        # Kimi (Moonshot AI)
        self.kimi_key = os.getenv("KIMI_API_KEY")
        if self.kimi_key and "sk-" in self.kimi_key and "9oXVX" not in self.kimi_key:
            self.kimi_client = openai.OpenAI(
                api_key=self.kimi_key,
                base_url="https://api.moonshot.cn/v1"
            )
        else:
            self.kimi_client = None
            
        # OpenRouter
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if self.openrouter_key and "your_openrouter" not in self.openrouter_key:
            self.openrouter_client = openai.OpenAI(
                api_key=self.openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.openrouter_client = None

        # Sambanova
        self.sambanova_key = os.getenv("SAMBANOVA_API_KEY")
        if self.sambanova_key and "your_sambanova" not in self.sambanova_key:
            self.sambanova_client = openai.OpenAI(
                api_key=self.sambanova_key,
                base_url="https://api.sambanova.ai/v1"
            )
        else:
            self.sambanova_client = None

    def get_prediction(self, match_info):
        user_message = match_info.get('message', 'Dame un pronóstico de fútbol')
        data_context = match_info.get('data_context', 'No hay datos adicionales disponibles')
        if isinstance(data_context, dict):
            data_context = str(data_context)
        
        # Integración de Simulación Monte Carlo para Córners
        monte_carlo_info = ""
        if "corner" in user_message.lower() or "esquina" in user_message.lower() or "pronóstico" in user_message.lower():
            # Realizamos predicción avanzada con ML (Random Forest)
            # Usando promedios de Bodø vs Inter como base
            ml_pred = StatsEngine.predict_advanced(1.2, 1.8, 4.65, 5.30)
            
            # También mantenemos la simulación Monte Carlo para probabilidad de Over
            sim = StatsEngine.simulate_corners(4.65, 5.30)
            
            monte_carlo_info = f"""
            --- PREDICCIÓN AVANZADA DE LIGA (RANDOM FOREST ML) ---
            Proyección Goles: {ml_pred['ml_goals']}
            Proyección Córners: {ml_pred['ml_corners']}

            --- SIMULACIÓN MONTE CARLO (PROBABILIDADES) ---
            Media Proyectada: {sim['media_simulada']}
            Probabilidad Over 8.5: {sim['probabilidades']['over_8_5']}%
            Probabilidad Over 9.5: {sim['probabilidades']['over_9_5']}%
            Probabilidad Over 10.5: {sim['probabilidades']['over_10_5']}%
            (Simulación basada en 10,000 iteraciones con errores estocásticos)
            """
            data_context += monte_carlo_info

        prompt = f"""
        Eres FutboltAI, un analista de fútbol especializado y EXCLUSIVO. 
        
        REGLA DE ORO DE SEGURIDAD:
        Solo tienes permitido responder preguntas relacionadas con el FÚTBOL (jugadores, equipos, ligas, tácticas, pronósticos, historia del fútbol, etc.).
        Si el usuario pregunta sobre CUALQUIER OTRO TEMA (política, ciencia, cine, otros deportes, consejos generales, etc.), debes declinar amablemente diciendo:
        "Lo siento, como FutboltAI mi especialidad es exclusivamente el análisis de fútbol. No puedo ayudarte con otros temas."

        DATOS DE CONTEXTO ACTUALES:
        {data_context}

        CONSULTA DEL USUARIO:
        {user_message}

        INSTRUCCIONES DE RESPUESTA (SI ES FÚTBOL):
        1. Utiliza los DATOS DE CONTEXTO y los datos de SIMULACIÓN MONTE CARLO (si están presentes) para fundamentar tus análisis.
        2. Formato:
           - ### 🏟️ Análisis de FutboltAI
           - **Marcador Probable**: [Equipo A] X - X [Equipo B]
           - **Probabilidades Victoria**: [X]% | [X]% | [X]%
           - **Análisis de Córners (Monte Carlo)**: Menciona las probabilidades de Over si la simulación está disponible.
           - **Key Insight**: Breve dato táctico o racha actual.
        3. Idioma: Español. Markdown activo.
        """

        # 1. Gemini (IA Principal - gemini-2.0-flash)
        if self.gemini_client:
            for model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
                try:
                    response = self.gemini_client.models.generate_content(model=model, contents=prompt)
                    return response.text + "\n\n*(Análisis impulsado por Gemini 2.0)*"
                except Exception:
                    continue

        # 2. Groq (Fallback 1 - Alta velocidad)
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content + "\n\n*(Análisis impulsado por Llama 3.3)*"
            except Exception as e:
                print(f"Groq Error: {e}")

        # 3. Mistral (Fallback 2)
        if self.mistral_client:
            try:
                response = self.mistral_client.chat.complete(
                    model="mistral-large-latest",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content + "\n\n*(Análisis impulsado por Mistral AI)*"
            except Exception as e:
                print(f"Mistral Error: {e}")

        # 4. OpenRouter
        if self.openrouter_client:
            try:
                response = self.openrouter_client.chat.completions.create(
                    model="openrouter/auto",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content + "\n\n*(Análisis impulsado por OpenRouter)*"
            except Exception as e:
                print(f"OpenRouter Error: {e}")

        # Fallback Final
        return """
### ⚠️ Modo de Reserva Activado
Actualmente las APIs de análisis están saturadas. 

**Basado en tendencias generales**: El equipo local suele tener una ventaja del 15% por factor campo. Recomendamos revisar las alineaciones oficiales 1 hora antes.
        """
