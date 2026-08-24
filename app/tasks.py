"""
SHUNYA OS — Task & Checklist Manager

Encapsulates all task/checklist CRUD behind a clean class facade.
Used by routes.py and available for programmatic access.
"""

from datetime import datetime, date, timezone
from typing import Optional
from app import db
from app.models import TaskList, Task
from sqlalchemy import func


class TaskManager:
    """Business logic for task lists and checklist items."""

    # ------------------------------------------------------------------
    # TaskList CRUD
    # ------------------------------------------------------------------

    def create_list(self, name: str, lead_id: Optional[int] = None,
                    created_by: str = "") -> TaskList:
        """Create a new task list (group/checklist)."""
        lst = TaskList(
            name=name.strip(),
            lead_id=lead_id,
            created_by=created_by or "",
        )
        db.session.add(lst)
        db.session.commit()
        return lst

    def delete_list(self, list_id: int) -> bool:
        """Delete a task list and all its tasks."""
        lst = db.session.get(TaskList, list_id)
        if not lst:
            return False
        db.session.delete(lst)
        db.session.commit()
        return True

    def get_list(self, list_id: int) -> Optional[TaskList]:
        """Get a single task list by id."""
        return db.session.get(TaskList, list_id)

    def get_all_lists(self) -> list[TaskList]:
        """Return all task lists ordered by creation date."""
        return TaskList.query.order_by(TaskList.created_at.desc()).all()

    # ------------------------------------------------------------------
    # Task CRUD
    # ------------------------------------------------------------------

    def add_task(self, list_id: int, title: str, description: str = "",
                 assigned_to: str = "", priority: str = "medium",
                 due_date: Optional[str] = None) -> Optional[Task]:
        """Add a task to a list. Returns the Task or None if list not found."""
        lst = db.session.get(TaskList, list_id)
        if not lst:
            return None

        parsed_due = None
        if due_date:
            try:
                parsed_due = datetime.strptime(due_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        # Determine next sort order
        max_order = (
            db.session.query(func.coalesce(func.max(Task.sort_order), -1))
            .filter(Task.task_list_id == list_id)
            .scalar()
        )

        task = Task(
            task_list_id=list_id,
            title=title.strip(),
            description=description,
            assigned_to=assigned_to,
            priority=priority,
            status="pending",
            sort_order=(max_order or 0) + 1,
            due_date=parsed_due,
        )
        db.session.add(task)
        db.session.commit()
        return task

    def update_status(self, task_id: int, new_status: str) -> Optional[Task]:
        """Update task status. Validates against allowed statuses."""
        allowed = {"pending", "in_progress", "completed", "cancelled"}
        if new_status not in allowed:
            return None

        task = db.session.get(Task, task_id)
        if not task:
            return None

        task.status = new_status
        if new_status == "completed":
            task.completed_at = datetime.now(timezone.utc)
        else:
            task.completed_at = None
        db.session.commit()
        return task

    def update_task(self, task_id: int, **kwargs) -> Optional[Task]:
        """Update arbitrary fields on a task (title, description, etc)."""
        task = db.session.get(Task, task_id)
        if not task:
            return None

        safe_keys = {"title", "description", "assigned_to", "priority",
                     "due_date", "sort_order"}
        for k, v in kwargs.items():
            if k in safe_keys:
                if k == "due_date" and v:
                    try:
                        v = datetime.strptime(v, "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        continue
                setattr(task, k, v)
        db.session.commit()
        return task

    def delete_task(self, task_id: int) -> bool:
        """Delete a single task."""
        task = db.session.get(Task, task_id)
        if not task:
            return False
        db.session.delete(task)
        db.session.commit()
        return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_for_user(self, user_id_or_name: str, limit: int = 50) -> list[Task]:
        """Get tasks assigned to a particular user."""
        return (
            Task.query
            .filter(Task.assigned_to == user_id_or_name)
            .order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_for_lead(self, lead_id: int) -> list[Task]:
        """Get all task lists (and their tasks) associated with a lead."""
        return (
            TaskList.query
            .filter(TaskList.lead_id == lead_id)
            .order_by(TaskList.created_at.desc())
            .all()
        )

    def get_tasks_for_list(self, list_id: int) -> list[Task]:
        """Get all tasks in a list, sorted by sort_order."""
        return (
            Task.query
            .filter(Task.task_list_id == list_id)
            .order_by(Task.sort_order.asc(), Task.created_at.asc())
            .all()
        )

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_statistics(self) -> dict:
        """Return aggregate task stats across all lists."""
        total = db.session.query(func.count(Task.id)).scalar() or 0
        pending = (
            db.session.query(func.count(Task.id))
            .filter(Task.status == "pending")
            .scalar() or 0
        )
        in_progress = (
            db.session.query(func.count(Task.id))
            .filter(Task.status == "in_progress")
            .scalar() or 0
        )
        completed = (
            db.session.query(func.count(Task.id))
            .filter(Task.status == "completed")
            .scalar() or 0
        )
        cancelled = (
            db.session.query(func.count(Task.id))
            .filter(Task.status == "cancelled")
            .scalar() or 0
        )
        overdue = (
            db.session.query(func.count(Task.id))
            .filter(
                Task.status.in_(["pending", "in_progress"]),
                Task.due_date < date.today(),
                Task.due_date.isnot(None),
            )
            .scalar() or 0
        )

        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "cancelled": cancelled,
            "overdue": overdue,
            "completion_rate": round(completed / total * 100, 1) if total else 0,
        }