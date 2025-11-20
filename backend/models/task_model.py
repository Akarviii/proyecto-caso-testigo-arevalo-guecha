# backend/models/task_model.py

class Task:
    def __init__(self, id: int, title: str, completed: bool = False):
        if not isinstance(id, int) or id <= 0:
            raise ValueError("Task ID must be a positive integer.")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Task title cannot be empty.")
        if not isinstance(completed, bool):
            raise ValueError("Task 'completed' status must be a boolean.")

        self.id = id
        self.title = title
        self.completed = completed

    def to_dict(self):
        """Converts the Task object to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "completed": self.completed
        }

    @staticmethod
    def from_dict(data: dict):
        """Creates a Task object from a dictionary."""
        if not all(k in data for k in ['id', 'title', 'completed']):
            raise ValueError("Dictionary must contain 'id', 'title', and 'completed' keys.")
        return Task(data['id'], data['title'], data['completed'])

    def __repr__(self):
        return f"Task(id={self.id}, title='{self.title}', completed={self.completed})"

    def __eq__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return self.id == other.id and self.title == other.title and self.completed == other.completed
