"""CSV persistence with atomic replacement and paths scoped to the task file."""
import csv
import os
from pathlib import Path
import tempfile


class Storage:
    def __init__(self, filename="tasks.txt"):
        self.path = Path(filename).resolve()
        self.directory = self.path.parent
        self.log_path = self.directory / "log.txt"
        self.date_path = self.directory / "last_log.txt"

    def load_tasks(self):
        if not self.path.exists():
            return None
        tasks, statuses = [], []
        with self.path.open(newline="", encoding="utf-8") as stream:
            for row in csv.reader(stream):
                if not row:
                    continue
                if len(row) != 2 or not row[0].strip() or row[1].strip().lower() not in {"true", "false"}:
                    raise ValueError(f"Invalid task record in {self.path.name}: {row!r}")
                tasks.append(row[0])
                statuses.append(row[1].strip().lower() == "true")
        return tasks, statuses

    @staticmethod
    def _replace(path, write):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as stream:
                write(stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def save_tasks(self, tasks, statuses):
        if len(tasks) != len(statuses):
            raise ValueError("Task and status counts must match")
        def write(stream):
            csv.writer(stream).writerows(zip(tasks, statuses))
        self._replace(self.path, write)

    def read_date(self):
        if not self.date_path.exists():
            return None
        return self.date_path.read_text(encoding="utf-8").strip()

    def save_date(self, value):
        self._replace(self.date_path, lambda stream: stream.write(value + "\n"))

    def log_history(self, day, tasks, statuses):
        self.directory.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(f"===== {day} =====\n")
            for name, done in zip(tasks, statuses):
                stream.write(f"Task:{name}, Status:{done}\n")
            stream.write("\n")
