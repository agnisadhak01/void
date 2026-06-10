from pydantic import BaseModel, Field


class PlanOutput(BaseModel):
    tasks: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


PLANNER_SYSTEM = """You are a software engineering planner. Given a user goal and optional context,
output ONLY valid JSON matching this schema:
{"tasks":["step1",...],"files":["paths"],"risks":["risk"],"dependencies":["dep"]}
Be specific and ordered. No markdown."""
