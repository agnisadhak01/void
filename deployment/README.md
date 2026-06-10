# Ausome AI Studio — Local Deployment

```powershell
cd X:\Void
docker compose -f deployment/docker-compose.yml up -d --build
```

Gateway: http://localhost:8000  
Health: http://localhost:8000/health  

Configure Pulse **Ausome Gateway** provider:

- Gateway URL: `http://127.0.0.1:8000`
- API Key: any value when `AUSOME_AUTH_DISABLED=true`

Optional vLLM on host port 8001 (see `infrastructure/helm/vllm`).
