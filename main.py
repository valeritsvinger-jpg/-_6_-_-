#uvicorn main:app --reload
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import utils

app = FastAPI()
tasks = []

class Task_create(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    priority: int = Field(3, ge=1, le=5)

class Task_update(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    priority: Optional[int] = Field(None, ge=1, le=5)
    is_done: Optional[bool] = None

class Task_read(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: int
    is_done: bool
    created_at: datetime

@app.post("/tasks", status_code=201)
async def create_task(task: Task_create):
    tasks = utils.read_tasks()

    if not tasks:
        new_id = 1
    else:
        new_id = max(t["id"] for t in tasks) + 1
    new_task = {
            "id": new_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "is_done": False,
            "created_at": datetime.now().isoformat()
        }

    tasks.append(new_task)
    utils.write_tasks(tasks)

    return new_task


@app.get("/tasks/{id}")
async def get_task_task(id: int):
    tasks = utils.read_tasks()
    task = next((t for t in tasks if t["id"] == id), None)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Задача с id {id} не найдена в нашей базе"
        )
    return task

@app.get("/tasks")
async def get_all_tasks(is_done: Optional[bool] = None, min_priority: Optional[int] = None):
    tasks = utils.read_tasks()

    if is_done is not None:
        tasks = [t for t in tasks if t["is_done"] == is_done]

    if min_priority is not None:
        tasks = [t for t in tasks if t["priority"] >= min_priority]

    return tasks


@app.patch("/tasks/{id}")
async def update_task(id: int, task_data: Task_update):
    tasks = utils.read_tasks()

    for number, t in enumerate(tasks):
        if t["id"] == id:
            update_dict = task_data.model_dump(exclude_unset=True)
            tasks[number].update(update_dict)
            utils.write_tasks(tasks)

            return tasks[number]

    raise HTTPException(status_code=404, detail="Задача не найдена")


@app.delete("/tasks/{id}")
async def delete_task(id: int):
    tasks = utils.read_tasks()

    task_exist = any(t["id"] == id for t in tasks)

    if not task_exist:
        raise HTTPException(status_code=404, detail="Нечего удалять, ID не найден")
    else:
        new_tasks = [t for t in tasks if t["id"] != id]
        utils.write_tasks(new_tasks)
        return {"status": "deleted", "id": id}
