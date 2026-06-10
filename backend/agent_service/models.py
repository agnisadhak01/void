from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    queued = "queued"
    planning = "planning"
    awaiting_approval = "awaiting_approval"
    executing = "executing"
    verifying = "verifying"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class AgentPhase(str, Enum):
    plan = "plan"
    code = "code"
    review = "review"
    test = "test"


class AgentRunRequest(BaseModel):
    goal: str
    session_id: str | None = None
    project_id: str = Field(default="00000000-0000-0000-0000-000000000001")
    messages: list[dict[str, Any]] = Field(default_factory=list)
    require_plan_approval: bool | None = None
    pulse_thread_id: str | None = None


class ToolResultRequest(BaseModel):
    tool_name: str
    result: str
    success: bool = True
    tool_call_id: str | None = None


class AgentRunResponse(BaseModel):
    run_id: str
    status: str
    phase: str | None = None
    plan: dict | None = None
    pending_tool: dict | None = None
    message: str | None = None
    steps: list[dict] = Field(default_factory=list)
