# Ausome AI Studio — Infrastructure

Kubernetes and Helm assets for production deployment. Local development uses [deployment/docker-compose.yml](../deployment/docker-compose.yml) instead.

## Layout

```
infrastructure/
  kubernetes/
    namespaces.yaml       # models, ausome, data namespaces
  helm/
    vllm/                 # vLLM inference Deployment + Service
    ausome-studio/        # Umbrella chart (gateway, workers) — M6 scaffold
```

## Quick deploy (cluster)

```bash
kubectl apply -f infrastructure/kubernetes/namespaces.yaml

# Inference (adjust values for your GPU nodes)
helm install vllm infrastructure/helm/vllm -n models --create-namespace

# Platform (when values are configured for your registry/secrets)
helm install ausome infrastructure/helm/ausome-studio -n ausome --create-namespace
```

## Gateway configuration

Point the API gateway at in-cluster vLLM:

```
VLLM_BASE_URL=http://ausome-vllm.models.svc.cluster.local:8000/v1
```

Production also requires:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Managed Postgres + pgvector |
| `AUSOME_AUTH_DISABLED=false` | Enforce JWT |
| `KEYCLOAK_JWKS_URL` / `KEYCLOAK_ISSUER` | OIDC (M14) |
| `MINIO_*` or S3-compatible | Workspace snapshots |
| `OPA_URL` | Policy sidecar |
| `SANDBOX_SERVICE_URL` | Isolated agent exec |

## Related

- [../deployment/README.md](../deployment/README.md) — Docker Compose dev stack
- [../docs/ausome/SECURITY.md](../docs/ausome/SECURITY.md)
- [../docs/ausome/ARCHITECTURE.md](../docs/ausome/ARCHITECTURE.md)
