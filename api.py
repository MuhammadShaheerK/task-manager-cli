"""Local single-process API. Importing this module does not create data files."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from core import TaskManager, TaskNotFoundError, TaskDoneAlreadyError, TaskAlreadyExists, InvalidTaskName
from services.task_services import TaskServices


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=500)


class TaskResponse(BaseModel):
    id: int
    name: str
    status: bool


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]


class TaskMutation(BaseModel):
    message: str
    task: TaskResponse


class TaskDeleted(BaseModel):
    message: str
    name: str


class Progress(BaseModel):
    completed: int
    total: int
    percent: float


def create_app(filename=None, today=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.service = TaskServices(TaskManager(filename, today))
        yield

    app = FastAPI(title="Task Manager", lifespan=lifespan)

    def call(operation, *args):
        try:
            return getattr(app.state.service, operation)(*args)
        except TaskNotFoundError:
            raise HTTPException(status_code=404, detail="Task not found") from None
        except TaskDoneAlreadyError:
            raise HTTPException(status_code=400, detail="Task already completed") from None
        except TaskAlreadyExists:
            raise HTTPException(status_code=400, detail="Task already exists") from None
        except InvalidTaskName as error:
            raise HTTPException(status_code=422, detail=str(error)) from None

    @app.get("/")
    def root():
        return {"message": "API is running!"}

    @app.get("/tasks", response_model=TaskListResponse)
    def list_tasks():
        return {"tasks": call("list_tasks")}

    @app.post("/tasks", response_model=TaskMutation, status_code=201)
    def add_task(task: TaskCreate):
        return {"message": "Task added successfully", "task": call("add_task", task.name)}

    @app.get("/tasks/{id}", response_model=TaskResponse)
    def get_task(id: int):
        return call("get_task", id)

    @app.put("/tasks/{id}/done", response_model=TaskMutation)
    def mark_task_done(id: int):
        return {"message": "Task completed", "task": call("mark_done", id)}

    @app.delete("/tasks/{id}", response_model=TaskDeleted)
    def delete_task(id: int):
        return {"message": "Task removed", "name": call("remove_task", id)["name"]}

    @app.get("/progress", response_model=Progress)
    def get_progress():
        return call("get_progress")

    return app


app = create_app()
