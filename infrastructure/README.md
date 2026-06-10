# Ausome AI Studio Infrastructure

```bash
kubectl apply -f infrastructure/kubernetes/namespaces.yaml
helm install vllm infrastructure/helm/vllm -n models --create-namespace
```

Set gateway `VLLM_BASE_URL=http://ausome-vllm.models.svc.cluster.local:8000/v1`.
