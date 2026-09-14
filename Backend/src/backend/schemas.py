from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.models import Priority, TaskStatus


class AuthCredentials(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "ada@example.com"})
    password: str = Field(..., json_schema_extra={"example": "focus"})


class UserResponse(BaseModel):
    id: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    id: str
    email: str
    token: str
    user: UserResponse


class CreateTaskInput(BaseModel):
    title: str = Field(..., min_length=1, json_schema_extra={"example": "Sketch onboarding flow"})
    description: str = Field(default="", json_schema_extra={"example": "Map the first three screens before writing any code."})
    dueDate: str = Field(default="", json_schema_extra={"example": "2026-03-20"})
    priority: Priority = Field(default=Priority.medium, json_schema_extra={"example": Priority.medium})
    status: TaskStatus = Field(..., json_schema_extra={"example": TaskStatus.ideas})


class UpdateTaskInput(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    dueDate: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None


class MoveTaskInput(BaseModel):
    status: TaskStatus = Field(..., description="Target column status")
    targetId: Optional[str] = Field(default=None, description="ID of task to insert before")
    position: Optional[int] = Field(default=None, description="Explicit target position index")


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    dueDate: str
    priority: Priority
    status: TaskStatus
    position: int
    completedAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    message: str
    code: Optional[str] = None
    statusCode: Optional[int] = None
