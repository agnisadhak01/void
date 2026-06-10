# Ausome API Gateway

FastAPI OpenAI-compatible gateway for Pulse editor.

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Environment: see `app/config.py`. Set `AUSOME_AUTH_DISABLED=true` for local dev.
