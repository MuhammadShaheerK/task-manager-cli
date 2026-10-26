"""Task operations shared by the CLI and API."""
from datetime import date
import os
from threading import RLock
from storage import Storage


class TaskNotFoundError(Exception):
    pass


class TaskDoneAlreadyError(Exception):
    pass


class TaskAlreadyExists(Exception):
    pass


class InvalidTaskName(ValueError):
    pass


class TaskManager:
    def __init__(self, filename=None, today=None):
        self.storage = Storage(filename or os.environ.get("TASK_MANAGER_FILE", "tasks.txt"))
        self.taskfile = str(self.storage.path)
        self._today = today or date.today
        self.lock = RLock()
        existing = self.storage.load_tasks()
        if existing is None:
            self.tasks, self.status = ["gym", "work", "study"], [False] * 3
            self.write_tasks_to_file()
        else:
            self.tasks, self.status = existing
        self.last_log_date = self.storage.read_date()
        if not self.last_log_date:
            self.last_log_date = self._today().isoformat()
            self.storage.save_date(self.last_log_date)

    def write_tasks_to_file(self):
        self.storage.save_tasks(self.tasks, self.status)

    def reset_tasks_to_default(self):
        self.tasks, self.status = ["gym", "work", "study"], [False] * 3
        self.write_tasks_to_file()

    def run(self):
        with self.lock:
            today = self._today().isoformat()
            if self.last_log_date != today:
                self.storage.log_history(self.last_log_date, self.tasks, self.status)
                self.reset_tasks_to_default()
                self.storage.save_date(today)
                self.last_log_date = today

    def _index(self, number):
        if number <= 0 or number > len(self.tasks):
            raise TaskNotFoundError()
        return number - 1

    def get_task(self, task_num):
        i = self._index(task_num)
        return {"id": task_num, "name": self.tasks[i], "status": self.status[i]}

    def add_task(self, task_name):
        name = task_name.strip()
        if not name or "\n" in name or "\r" in name:
            raise InvalidTaskName("Use a non-empty, single-line task name")
        if any(name.casefold() == old.casefold() for old in self.tasks):
            raise TaskAlreadyExists()
        self.tasks.append(name)
        self.status.append(False)
        self.write_tasks_to_file()
        return self.get_task(len(self.tasks))

    def update_tasks(self, task_num):
        i = self._index(task_num)
        if self.status[i]:
            raise TaskDoneAlreadyError()
        self.status[i] = True
        self.write_tasks_to_file()
        return self.get_task(task_num)

    def remove_task(self, task_num):
        removed = self.get_task(task_num)
        i = self._index(task_num)
        self.tasks.pop(i)
        self.status.pop(i)
        self.write_tasks_to_file()
        return removed

    def cal_progress(self):
        return sum(self.status), len(self.tasks)
