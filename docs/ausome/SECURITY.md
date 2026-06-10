# Ausome AI Studio — Security

## Principles

- **Gateway-only inference:** Production Pulse builds route all model traffic through `backend/api-gateway`. No direct cloud API keys in enterprise mode.
- **Authentication:** Supabase JWT on every API request (`Authorization: Bearer`).
- **RBAC:** Roles enforced at gateway — `admin`, `developer`, `viewer`.
- **Audit:** Append-only `audit_logs` for agent actions, terminal commands, and file mutations.
- **Sandbox:** Agent terminal commands run in Docker containers when `AUSOME_SANDBOX_ENABLED=true` (not on host).
- **Secrets:** Use K8s Secrets / Vault in production; never commit `.env` with real keys.

## Development exceptions

- `AUSOME_AUTH_DISABLED=true` allows local gateway testing without Supabase.
- Direct cloud providers remain in Pulse for dev fallback until enterprise profile is enabled.

## Compliance checklist

- [ ] JWT validation on all `/v1/*` routes
- [ ] Audit log retention policy defined
- [ ] Sandbox network isolation verified
- [ ] RBAC tested per role
- [ ] Cursor proprietary bundles not redistributed (reference only)
