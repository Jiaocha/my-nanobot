"""Cron tool for scheduling reminders and tasks."""

from typing import Any

# 本地化支持
from localization import get_translation as _t
from nanobot.agent.tools.base import Tool
from nanobot.cron.service import CronService
from nanobot.cron.types import CronSchedule


class CronTool(Tool):
    """Tool to schedule reminders and recurring tasks."""

    def __init__(self, cron_service: CronService):
        self._cron = cron_service
        self._channel = ""
        self._chat_id = ""

    def set_context(self, channel: str, chat_id: str) -> None:
        """Set the current session context for delivery."""
        self._channel = channel
        self._chat_id = chat_id

    @property
    def name(self) -> str:
        return _t("agent.tools.cron.name", "cron")

    @property
    def description(self) -> str:
        return _t("agent.tools.cron.description", "Schedule reminders and recurring tasks. Actions: add, list, remove.")

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "list", "remove"],
                    "description": _t("agent.tools.cron.params.action", "Action to perform"),
                },
                "message": {"type": "string", "description": _t("agent.tools.cron.params.message", "Reminder message (for add)")},
                "every_seconds": {
                    "type": "integer",
                    "description": _t("agent.tools.cron.params.every_seconds", "Interval in seconds (for recurring tasks)"),
                },
                "cron_expr": {
                    "type": "string",
                    "description": _t("agent.tools.cron.params.cron_expr", "Cron expression like '0 9 * * *' (for scheduled tasks)"),
                },
                "tz": {
                    "type": "string",
                    "description": _t("agent.tools.cron.params.tz", "IANA timezone for cron expressions (e.g. 'America/Vancouver')"),
                },
                "at": {
                    "type": "string",
                    "description": _t("agent.tools.cron.params.at", "ISO datetime for one-time execution (e.g. '2026-02-12T10:30:00')"),
                },
                "job_id": {"type": "string", "description": _t("agent.tools.cron.params.job_id", "Job ID (for remove)")},
            },
            "required": ["action"],
        }

    async def execute(
        self,
        action: str,
        message: str = "",
        every_seconds: int | None = None,
        cron_expr: str | None = None,
        tz: str | None = None,
        at: str | None = None,
        job_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        if action == "add":
            return self._add_job(message, every_seconds, cron_expr, tz, at)
        elif action == "list":
            return self._list_jobs()
        elif action == "remove":
            return self._remove_job(job_id)
        return f"Unknown action: {action}"

    def _add_job(
        self,
        message: str,
        every_seconds: int | None,
        cron_expr: str | None,
        tz: str | None,
        at: str | None,
    ) -> str:
        if not message:
            return _t("agent.tools.cron.error.message_required", "Error: message is required for add")
        if not self._channel or not self._chat_id:
            return _t("agent.tools.cron.error.no_session_context", "Error: no session context (channel/chat_id)")
        if tz and not cron_expr:
            return _t("agent.tools.cron.error.tz_without_cron", "Error: tz can only be used with cron_expr")
        if tz:
            from zoneinfo import ZoneInfo

            try:
                ZoneInfo(tz)
            except (KeyError, Exception):
                return _t("agent.tools.cron.error.unknown_timezone", f"Error: unknown timezone '{tz}'")

        # Build schedule
        delete_after = False
        if every_seconds:
            schedule = CronSchedule(kind="every", every_ms=every_seconds * 1000)
        elif cron_expr:
            schedule = CronSchedule(kind="cron", expr=cron_expr, tz=tz)
        elif at:
            from datetime import datetime

            dt = datetime.fromisoformat(at)
            at_ms = int(dt.timestamp() * 1000)
            schedule = CronSchedule(kind="at", at_ms=at_ms)
            delete_after = True
        else:
            return _t("agent.tools.cron.error.schedule_required", "Error: either every_seconds, cron_expr, or at is required")

        job = self._cron.add_job(
            name=message[:30],
            schedule=schedule,
            message=message,
            deliver=True,
            channel=self._channel,
            to=self._chat_id,
            delete_after_run=delete_after,
        )
        return _t("agent.tools.cron.messages.job_added", f"Created job '{job.name}' (id: {job.id})")

    def _list_jobs(self) -> str:
        jobs = self._cron.list_jobs()
        if not jobs:
            return _t("agent.tools.cron.messages.no_jobs", "No scheduled jobs.")
        lines = [f"- {j.name} (id: {j.id}, {j.schedule.kind})" for j in jobs]
        return _t("agent.tools.cron.messages.scheduled_jobs", "Scheduled jobs:\n") + "\n".join(lines)

    def _remove_job(self, job_id: str | None) -> str:
        if not job_id:
            return _t("agent.tools.cron.error.job_id_required", "Error: job_id is required for remove")
        if self._cron.remove_job(job_id):
            return _t("agent.tools.cron.messages.job_removed", f"Removed job {job_id}")
        return _t("agent.tools.cron.error.job_not_found", f"Job {job_id} not found")
