# Ausome AI Studio — Security

## Principles

- **Gateway-only inference:** Production Pulse builds route all model traffic through `backend/api-gateway`. No direct cloud API keys in enterprise mode.
- **Authentication:** Supabase JWT (HS256) or Keycloak OIDC (JWKS) on every API request (`Authorization: Bearer`).
- **RBAC:** Roles enforced at gateway — `admin`, `developer`, `viewer`. Keycloak groups map to roles when `KEYCLOAK_JWKS_URL` is set.
- **Audit:** Append-only `audit_logs` and `agent_run_steps` for agent actions, terminal commands, and file mutations.
- **Sandbox:** Agent terminal commands run in Docker containers when `AUSOME_SANDBOX_ENABLED=true` (not on host).
- **Secrets:** Use K8s Secrets / Vault in production; never commit `.env` with real keys.

## M14 production controls

| Control | Configuration |
|---------|----------------|
| OIDC | `KEYCLOAK_JWKS_URL`, `KEYCLOAK_ISSUER` — replaces dev-only auth when `AUSOME_AUTH_DISABLED=false` |
| OPA | `OPA_URL` — middleware denies `/v1/agent/*` when policy returns `false` |
| Rate limiting | `RATE_LIMIT_PER_MINUTE` (default 120) — token bucket per client IP |
| Snapshots | MinIO `MINIO_*` — pre-agent workspace manifests for rollback |
| Eval gate | Agent runs cannot reach `completed` if sandbox checks fail (admin override) |

## Development exceptions

- `AUSOME_AUTH_DISABLED=true` allows local gateway testing without Supabase/Keycloak.
- Direct cloud providers remain in Pulse for dev fallback until enterprise profile is enabled.

## Compliance checklist

- [x] JWT validation on all `/v1/*` routes (Supabase or Keycloak)
- [x] RBAC `require_role` on mutating endpoints
- [x] Audit log writes on agent runs and LLM calls
- [x] OPA hook for agent routes (enable with `OPA_URL`)
- [x] Rate limiting middleware
- [ ] Audit log retention policy defined
- [ ] Sandbox network isolation verified in production
- [ ] RBAC tested per role in staging
- [ ] Cursor proprietary bundles not redistributed (reference only)

## OPA policy example

Deploy OPA with a rule at `data.ausome.allow`:

```rego
package ausome

default allow = true

deny_tool_exec_on_host {
  input.path == "/v1/agent/run"
  input.role != "admin"
}

allow {
  not deny_tool_exec_on_host
}
```

Post evaluations to `{OPA_URL}/v1/data/ausome/allow`.
