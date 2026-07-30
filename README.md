# Futbol_predictor

Predictor de fútbol con Flask: partidos del día, estadísticas, combinadas y predicciones con IA.

## Arranque local

```bash
python -m pip install -r requirements.txt
cp .env.example .env   # completar API keys
python app.py
```

Abre http://127.0.0.1:5001

## Despliegue en Render (todo online)

### 1. Repo
El código ya está en: https://github.com/sistemashsja-jr/Futbol_predictor

### 2. Crear el servicio
1. Entra en https://dashboard.render.com con la cuenta GitHub `sistemashsja-jr`.
2. **New** → **Blueprint** (usa `render.yaml`) **o** **Web Service** → repo `Futbol_predictor`.
3. Si usas Web Service manual:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`

### 3. Variables de entorno (Environment)
Copia los valores de tu `.env` local (nunca subas el `.env` a GitHub):

| Variable | ¿Obligatoria? |
|----------|----------------|
| `FLASK_SECRET_KEY` | Sí (Render puede generarla) |
| `GEMINI_API_KEY` | Sí para predicciones IA |
| `FOOTBALL_DATA_API_KEY` | Recomendada |
| `APISPORTS_API_KEY` | Opcional |
| `GROQ_API_KEY` / `OPENROUTER_API_KEY` / … | Opcionales (fallback IA) |
| `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` | Solo si quieres login Google |

### 4. Google OAuth (si usas login)
En Google Cloud Console → URI de redirección autorizada:

`https://TU-SERVICIO.onrender.com/auth/google/callback`

### 5. Probar
- Home: `https://TU-SERVICIO.onrender.com/`
- Health: `https://TU-SERVICIO.onrender.com/health`

**Notas del plan free:** cold start ~30–60 s; SQLite se borra al redeploy; Obsidian no aplica en la nube (solo en tu PC).
