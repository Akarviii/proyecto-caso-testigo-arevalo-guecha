# backend/services/task_service.py
from models.task_model import Task # Import the Task class

tasks: list[Task] = []
task_id_counter = 1

def _reset_state():
    """Resets the in-memory task storage for testing purposes."""
    global tasks
    global task_id_counter
    tasks = []
    task_id_counter = 1

def get_all_tasks() -> list[Task]:
    """Returns all tasks."""
    return list(tasks) # Return a copy to prevent external modification

def get_task_by_id(task_id: int) -> Task | None:
    """Returns a task by its ID."""
    return next((t for t in tasks if t.id == task_id), None)

def create_task(title: str, completed: bool = False) -> Task:
    """Creates a new task and returns it."""
    global task_id_counter
    new_task = Task(id=task_id_counter, title=title, completed=completed)
    tasks.append(new_task)
    task_id_counter += 1
    return new_task

def update_task(task_id: int, title: str | None = None, completed: bool | None = None) -> Task | None:
    """Updates an existing task and returns the updated task."""
    task = get_task_by_id(task_id)
    if task:
        if title is not None:
            task.title = title
        if completed is not None:
            task.completed = completed
    return task

def delete_task(task_id: int) -> bool:
    """Deletes a task by its ID. Returns True if deleted, False otherwise."""
    global tasks
    initial_len = len(tasks)
    tasks = [t for t in tasks if t.id != task_id]
    return len(tasks) < initial_len # Returns True if a task was deleted
