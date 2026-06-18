#!/usr/bin/env python3
"""Query hashbuild task/step filesystem structure. All output is JSON.

Subcommands:
  list                      # active task IDs
  archive                   # archived task IDs
  status <task-id>          # task status + step list
  steps <task-id>           # step IDs for a task
  next-task-id              # next available TASK-NNN id
  next-step-id <task-id>    # next available STEP-NNN id within a task
"""
import json
import sys
import argparse
from pathlib import Path

TASKS_ROOT = Path("tasks")


def _sorted_ids(directory: Path) -> list[str]:
    if not directory.exists():
        return []
    return sorted(d.name for d in directory.iterdir() if d.is_dir())


def list_active() -> list[str]:
    return _sorted_ids(TASKS_ROOT / "active")


def list_archived() -> list[str]:
    return _sorted_ids(TASKS_ROOT / "archive")


def list_steps(task_id: str) -> list[str]:
    return _sorted_ids(TASKS_ROOT / "active" / task_id / "steps")


def task_status(task_id: str) -> dict:
    active_path = TASKS_ROOT / "active" / task_id
    archive_path = TASKS_ROOT / "archive" / task_id

    if active_path.exists():
        steps = list_steps(task_id)
        return {"task_id": task_id, "status": "active", "path": str(active_path), "steps": steps}
    if archive_path.exists():
        return {"task_id": task_id, "status": "archived", "path": str(archive_path)}
    return {"task_id": task_id, "status": "not_found"}


def next_task_id() -> str:
    existing = list_active() + list_archived()
    nums = []
    for name in existing:
        if name.startswith("TASK-") and name[5:].isdigit():
            nums.append(int(name[5:]))
    n = max(nums) + 1 if nums else 1
    return f"TASK-{n:03d}"


def next_step_id(task_id: str) -> str:
    existing = list_steps(task_id)
    nums = []
    for name in existing:
        if name.startswith("STEP-") and name[5:].isdigit():
            nums.append(int(name[5:]))
    n = max(nums) + 1 if nums else 1
    return f"STEP-{n:03d}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query hashbuild task structure")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List active tasks")
    sub.add_parser("archive", help="List archived tasks")
    sub.add_parser("next-task-id", help="Next available task ID")

    p_status = sub.add_parser("status", help="Task status")
    p_status.add_argument("task_id")

    p_steps = sub.add_parser("steps", help="List steps")
    p_steps.add_argument("task_id")

    p_nstep = sub.add_parser("next-step-id", help="Next available step ID")
    p_nstep.add_argument("task_id")

    args = parser.parse_args()

    if args.cmd == "list":
        print(json.dumps(list_active()))
    elif args.cmd == "archive":
        print(json.dumps(list_archived()))
    elif args.cmd == "status":
        print(json.dumps(task_status(args.task_id)))
    elif args.cmd == "steps":
        print(json.dumps(list_steps(args.task_id)))
    elif args.cmd == "next-task-id":
        print(json.dumps(next_task_id()))
    elif args.cmd == "next-step-id":
        print(json.dumps(next_step_id(args.task_id)))
