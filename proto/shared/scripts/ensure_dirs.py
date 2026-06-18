#!/usr/bin/env python3
"""Ensure hashbuild task/step directory structure exists.

Usage:
  ensure_dirs.py <task-id>                    # creates tasks/active/TASK-001/ + steps/
  ensure_dirs.py <task-id> --step <step-id>   # creates tasks/active/TASK-001/steps/STEP-001/ + execution/
  ensure_dirs.py <task-id> --archive          # creates tasks/archive/TASK-001/
"""
import sys
import argparse
from pathlib import Path

TASKS_ROOT = Path("tasks")


def ensure_task_dir(task_id: str) -> Path:
    task_dir = TASKS_ROOT / "active" / task_id
    (task_dir / "steps").mkdir(parents=True, exist_ok=True)
    return task_dir


def ensure_step_dir(task_id: str, step_id: str) -> Path:
    step_dir = TASKS_ROOT / "active" / task_id / "steps" / step_id
    (step_dir / "execution").mkdir(parents=True, exist_ok=True)
    return step_dir


def ensure_archive_dir(task_id: str) -> Path:
    archive_dir = TASKS_ROOT / "archive" / task_id
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ensure hashbuild directory structure")
    parser.add_argument("task_id", help="Task ID (e.g., TASK-001)")
    parser.add_argument("--step", metavar="STEP_ID", help="Step ID (e.g., STEP-001)")
    parser.add_argument("--archive", action="store_true", help="Ensure archive dir instead of active")
    args = parser.parse_args()

    if args.archive:
        path = ensure_archive_dir(args.task_id)
    elif args.step:
        path = ensure_step_dir(args.task_id, args.step)
    else:
        path = ensure_task_dir(args.task_id)

    print(str(path))
