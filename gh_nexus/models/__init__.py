from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    BACKLOG = "Backlog"
    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    BLOCKED = "Blocked"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class AgentType(str, Enum):
    OPENCODE = "opencode"
    CLAUDE_CODE = "claude-code"
    CURSOR = "cursor"
    WIND_SURF = "windsurf"
    GITHUB_COPILOT = "github-copilot"
    CUSTOM = "custom"


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    github_issue_id: Optional[int] = None
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    labels: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    parent_id: Optional[UUID] = None
    subtasks: list[UUID] = Field(default_factory=list)

    worker_id: Optional[UUID] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0

    def mark_done(self) -> None:
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    def assign_worker(self, worker_id: UUID) -> None:
        self.worker_id = worker_id
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now()


class Worker(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    agent_type: AgentType
    status: str = "idle"
    current_task_id: Optional[UUID] = None
    capabilities: list[str] = Field(default_factory=list)
    api_key: Optional[str] = None
    endpoint: Optional[str] = None

    is_available: bool = True
    max_concurrent_tasks: int = 1
    success_rate: float = 1.0
    total_tasks_completed: int = 0


class ProjectGoal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)
    target_date: Optional[datetime] = None
    progress: float = 0.0


class TaskResult(BaseModel):
    task_id: UUID
    worker_id: UUID
    status: str
    output: str = ""
    quality_score: float = 0.0
    duration_seconds: float = 0.0
    errors: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    sender: str
    recipient: str
    content: str
    task_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.now)
    read: bool = False
