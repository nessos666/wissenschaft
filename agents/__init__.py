"""Base Agent — gemeinsame Schnittstelle für alle Agenten."""
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AgentResult:
    agent_name: str
    success: bool
    data: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0.0

class BaseAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
    
    def run(self, input_data: dict) -> AgentResult:
        raise NotImplementedError
    
    def log(self, msg: str):
        print(f"[{self.name}] {msg}")
    
    def ok(self, data: dict, duration: float = 0) -> AgentResult:
        return AgentResult(agent_name=self.name, success=True, data=data, duration_ms=duration)
    
    def fail(self, errors: list[str]) -> AgentResult:
        return AgentResult(agent_name=self.name, success=False, errors=errors)
