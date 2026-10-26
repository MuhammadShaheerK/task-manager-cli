"""Synchronize access and check day rollover before every operation."""
class TaskServices:
    def __init__(self, manager):
        self.manager = manager

    def _call(self, operation, *args):
        with self.manager.lock:
            self.manager.run()
            return operation(*args)

    def list_tasks(self):
        return self._call(lambda: [self.manager.get_task(i + 1) for i in range(len(self.manager.tasks))])

    def reset_tasks(self):
        self._call(self.manager.reset_tasks_to_default)

    def mark_done(self, task_num):
        return self._call(self.manager.update_tasks, task_num)

    def add_task(self, task_name):
        return self._call(self.manager.add_task, task_name)

    def remove_task(self, task_num):
        return self._call(self.manager.remove_task, task_num)

    def get_task(self, task_num):
        return self._call(self.manager.get_task, task_num)

    def get_progress(self):
        def progress():
            completed, total = self.manager.cal_progress()
            return {"completed": completed, "total": total,
                    "percent": round(100 * completed / total) if total else 0}
        return self._call(progress)
