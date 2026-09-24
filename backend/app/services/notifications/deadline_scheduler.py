import logging
import threading

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.database import SessionLocal
from app.services.notifications.notification_service import process_tender_deadline_reminders

logger = logging.getLogger(__name__)
_stop_event = threading.Event()
_worker: threading.Thread | None = None


def _run() -> None:
    while not _stop_event.is_set():
        db = SessionLocal()
        try:
            process_tender_deadline_reminders(db)
        except SQLAlchemyError:
            logger.exception("Deadline reminder processing failed")
        finally:
            db.close()
        _stop_event.wait(max(1, settings.DEADLINE_REMINDER_INTERVAL_SECONDS))


def start_deadline_scheduler() -> None:
    global _worker
    if _worker and _worker.is_alive():
        return
    _stop_event.clear()
    _worker = threading.Thread(
        target=_run,
        name="bharatsetu-deadline-reminders",
        daemon=True,
    )
    _worker.start()


def stop_deadline_scheduler() -> None:
    _stop_event.set()
