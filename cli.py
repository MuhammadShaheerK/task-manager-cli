"""Command-line interface; run python main.py --help."""
import argparse
import json
from core import TaskManager, TaskNotFoundError, TaskDoneAlreadyError, TaskAlreadyExists
from services.task_services import TaskServices


def run_cli(argv=None):
    parser = argparse.ArgumentParser(description="Daily task manager (local file storage)")
    parser.add_argument("--file", help="Task CSV path; defaults to TASK_MANAGER_FILE or tasks.txt")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("tasks", aliases=["list"])
    commands.add_parser("progress")
    commands.add_parser("reset")
    add = commands.add_parser("add")
    add.add_argument("name")
    for command in ("done", "remove"):
        child = commands.add_parser(command)
        child.add_argument("number", type=int)
    args = parser.parse_args(argv)
    try:
        service = TaskServices(TaskManager(filename=args.file))
        actions = {
            "tasks": service.list_tasks, "list": service.list_tasks,
            "progress": service.get_progress, "reset": service.reset_tasks,
            "add": lambda: service.add_task(args.name),
            "done": lambda: service.mark_done(args.number),
            "remove": lambda: service.remove_task(args.number),
        }
        result = actions[args.command]()
        print(json.dumps(result if result is not None else {"message": "Tasks reset"}, indent=2))
    except TaskNotFoundError:
        parser.error("Task number does not exist")
    except TaskDoneAlreadyError:
        parser.error("Task is already completed")
    except TaskAlreadyExists:
        parser.error("Task already exists")
    except (ValueError, OSError) as error:
        parser.error(str(error))
