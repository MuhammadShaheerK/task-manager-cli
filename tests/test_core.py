from datetime import date
import pytest
from core import TaskManager, TaskDoneAlreadyError, TaskAlreadyExists, InvalidTaskName
from services.task_services import TaskServices


def test_defaults_and_persistence(tmp_path):
    path = tmp_path / "tasks.txt"
    manager = TaskManager(path)
    assert manager.tasks == ["gym", "work", "study"]
    manager.update_tasks(1)
    assert TaskManager(path).status == [True, False, False]


def test_quoted_name_round_trip(tmp_path):
    path = tmp_path / "tasks.txt"
    manager = TaskManager(path)
    task = manager.add_task('read, "learn"')
    assert TaskManager(path).get_task(task["id"])["name"] == 'read, "learn"'


def test_empty_list_remains_empty_on_restart(tmp_path):
    path = tmp_path / "tasks.txt"
    manager = TaskManager(path)
    for _ in range(3):
        manager.remove_task(1)
    assert TaskManager(path).tasks == []
    assert TaskServices(TaskManager(path)).get_progress()["percent"] == 0


def test_errors(tmp_path):
    manager = TaskManager(tmp_path / "tasks.txt")
    with pytest.raises(InvalidTaskName):
        manager.add_task("  ")
    with pytest.raises(InvalidTaskName):
        manager.add_task("a\nb")
    with pytest.raises(TaskAlreadyExists):
        manager.add_task(" GYM ")
    manager.update_tasks(1)
    with pytest.raises(TaskDoneAlreadyError):
        manager.update_tasks(1)


def test_malformed_storage_is_rejected_without_rewriting(tmp_path):
    path = tmp_path / "tasks.txt"
    path.write_text("gym,invalid\n", encoding="utf-8")
    with pytest.raises(ValueError):
        TaskManager(path)
    assert path.read_text() == "gym,invalid\n"


def test_day_rollover_during_running_service(tmp_path):
    day = [date(2026, 1, 1)]
    manager = TaskManager(tmp_path / "tasks.txt", today=lambda: day[0])
    service = TaskServices(manager)
    service.mark_done(1)
    day[0] = date(2026, 1, 2)
    assert service.get_progress() == {"completed": 0, "total": 3, "percent": 0}
    assert "Task:gym, Status:True" in (tmp_path / "log.txt").read_text()
    assert (tmp_path / "last_log.txt").read_text().strip() == "2026-01-02"
    service.get_progress()
    assert (tmp_path / "log.txt").read_text().count("=====") == 2
