from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.auth import get_current_user
from backend.models import User
from backend.schemas import CreateTaskInput, MoveTaskInput, TaskResponse, UpdateTaskInput
from backend.store import store

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=List[TaskResponse])
def list_tasks(current_user: User = Depends(get_current_user)) -> List[TaskResponse]:
    tasks = store.get_tasks(current_user.id)
    return [TaskResponse.model_validate(t) for t in tasks]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    input_data: CreateTaskInput,
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    if not input_data.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A task needs a title.",
        )

    task = store.create_task(
        user_id=current_user.id,
        title=input_data.title,
        description=input_data.description,
        due_date=input_data.dueDate,
        priority=input_data.priority,
        status=input_data.status,
    )
    return TaskResponse.model_validate(task)


@router.delete("/completed", status_code=status.HTTP_204_NO_CONTENT)
def clear_completed(current_user: User = Depends(get_current_user)) -> Response:
    store.clear_completed(current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}", response_model=TaskResponse)
def get_task(
    id: str,
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    task = store.get_task(current_user.id, id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That task is no longer available.",
        )
    return TaskResponse.model_validate(task)


@router.patch("/{id}", response_model=TaskResponse)
def update_task(
    id: str,
    input_data: UpdateTaskInput,
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    if input_data.title is not None and not input_data.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A task needs a title.",
        )

    updated = store.update_task(
        user_id=current_user.id,
        task_id=id,
        title=input_data.title,
        description=input_data.description,
        due_date=input_data.dueDate,
        priority=input_data.priority,
        status=input_data.status,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That task is no longer available.",
        )
    return TaskResponse.model_validate(updated)


@router.post("/{id}/move", response_model=List[TaskResponse])
def move_task(
    id: str,
    input_data: MoveTaskInput,
    current_user: User = Depends(get_current_user),
) -> List[TaskResponse]:
    updated_tasks = store.move_task(
        user_id=current_user.id,
        task_id=id,
        status=input_data.status,
        target_id=input_data.targetId,
        position=input_data.position,
    )
    if updated_tasks is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That task is no longer available.",
        )
    return [TaskResponse.model_validate(t) for t in updated_tasks]


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    id: str,
    current_user: User = Depends(get_current_user),
) -> Response:
    deleted = store.delete_task(current_user.id, id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That task is no longer available.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
