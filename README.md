# Futbol_predictor

Predictor de fútbol con Flask: partidos del día, estadísticas, combinadas y predicciones con IA.

## Arranque local

```bash
pip install -r requirements.txt
cp .env.example .env   # completar API keys
python app.py
```

La app escucha en el puerto `5001` (o `PORT` si está definido).

## Despliegue en Render (desde GitHub)

1. Entra en [https://dashboard.render.com](https://dashboard.render.com) e inicia sesión con GitHub (`sistemashsja-jr`).
2. **New** → **Web Service** → conecta el repo `Futbol_predictor`.
3. Ajustes:
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
   - (si Render detecta el `Procfile`, el start command se rellena solo)
4. En **Environment** añade las variables de `.env.example` (al menos `FLASK_SECRET_KEY`, y las API keys que uses).
5. **Create Web Service** y espera el deploy.
6. Cuando tengas la URL (`https://….onrender.com`), en Google Cloud Console añade esa URI de callback:
   `https://TU-SERVICIO.onrender.com/auth/google/callback`

En el plan free el servicio se duerme tras inactividad; la primera visita puede tardar ~1 minuto. SQLite (`predictions.db`) se pierde al redeploy.
