# Task Manager: CLI + FastAPI

A local daily task manager with a shared service layer, CSV persistence, a command-line interface, and a REST API.

## Setup

Python 3.12, from the repository root:

~~~bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux, instead:
# source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
~~~

## Command-line use

~~~bash
python main.py list
python main.py add "Read, write, and review"
python main.py done 1
python main.py progress
python main.py remove 2
python main.py reset
~~~

Every command prints JSON. Invalid input exits with a readable error and a nonzero status. The tasks command is an alias for list.

For another data location:

~~~bash
python main.py --file data/tasks.txt list
~~~

The --file option goes before the command. TASK_MANAGER_FILE is also supported; the command-line option takes precedence.

## API

~~~bash
python -m uvicorn api:app --reload
~~~

Open http://127.0.0.1:8000/docs for interactive documentation.

| Method | Route | Behavior |
|---|---|---|
| GET | /tasks | List tasks and current positional IDs |
| POST | /tasks | Add a task; JSON body: {"name": "Read"} |
| GET | /tasks/{id} | Retrieve a task |
| PUT | /tasks/{id}/done | Mark it completed |
| DELETE | /tasks/{id} | Remove it |
| GET | /progress | Completed count, total, and percent |

The API initializes storage on startup, not module import. It checks the day before each service operation, including while the server stays running overnight.

## Storage and behavior

- First use creates gym, work, and study. Removing every task preserves an empty list on restart that same day.
- tasks.txt is CSV despite its extension. CSV quoting preserves commas and quotes in names; existing valid two-column task files remain readable.
- Empty/whitespace-only or multi-line names are rejected; duplicate names are checked case-insensitively.
- Tasks remain in insertion order. IDs are 1-based list positions, not permanent identifiers. Deleting a task changes later IDs; refresh the list before the next action.
- On the first operation on a new local calendar day, the previous state is appended to log.txt and the list resets to the default three tasks. The reset command performs the same default reset immediately.
- log.txt and last_log.txt live beside the chosen task file. Use separate directories for independent task stores.
- Writes use temporary files followed by atomic replacement. Malformed rows raise an error instead of silently truncating the task/status lists.

## Structure

- core.py: task rules and daily rollover.
- storage.py: CSV loading, atomic replacement, and history files.
- services/task_services.py: shared synchronized operations.
- cli.py / main.py: CLI parser and entry point.
- api.py: app factory, validation, and HTTP error handling.
- tests/: persistence, validation, day rollover, API CRUD/errors, CLI output, and import-side-effect checks.

## Scope

This is a local, single-process learning application. API operations share an in-process lock; multiple server workers or simultaneous CLI/API processes writing the same files are not supported. It has no authentication and should stay bound to localhost. Atomic individual file writes do not make day rollover across three files a crash-safe transaction. A database would be the next step for those requirements.
