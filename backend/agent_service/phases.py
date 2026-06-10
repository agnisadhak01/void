"""Multi-agent phase transitions (M12)."""

from agent_service.models import AgentPhase, RunStatus

PHASE_ORDER = [AgentPhase.plan, AgentPhase.code, AgentPhase.review, AgentPhase.test]


def next_phase(current: str) -> str | None:
    try:
        idx = PHASE_ORDER.index(AgentPhase(current))
    except ValueError:
        return AgentPhase.code.value
    if idx + 1 < len(PHASE_ORDER):
        return PHASE_ORDER[idx + 1].value
    return None


def phase_status_after_plan(require_approval: bool) -> RunStatus:
    return RunStatus.awaiting_approval if require_approval else RunStatus.executing


def status_for_phase(phase: str) -> RunStatus:
    if phase == AgentPhase.test.value:
        return RunStatus.verifying
    return RunStatus.executing
