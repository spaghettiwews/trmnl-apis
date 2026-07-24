import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from caldav import DAVClient
from dateutil.parser import parse
from dotenv import load_dotenv
from flask import Blueprint, jsonify

import helpers

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

CALENDAR_URL: Optional[str] = os.getenv("CALENDAR_URL")
CALENDAR_USER: Optional[str] = os.getenv("CALENDAR_USER")
CALENDAR_PASSWORD: Optional[str] = os.getenv("CALENDAR_PASSWORD")
CALENDAR_ID: Optional[str] = os.getenv("CALENDAR_ID")
DAYS_AHEAD: Optional[int] = int(os.getenv("DAYS_AHEAD", "1"))
TIMEOUT: Optional[int] = int(os.getenv("TIMEOUT", "60"))

todos_bp = Blueprint("todos", __name__, url_prefix="/")


def fetch_from_calendar() -> Dict[str, List[Dict[str, Any]]]:

    if not all([CALENDAR_URL, CALENDAR_USER, CALENDAR_PASSWORD, CALENDAR_ID]):
        logger.error("Missing environment variables required for CalDAV connection.")
        raise EnvironmentError(
            "CalDAV credentials are not fully set in the environment."
        )

    try:
        client = DAVClient(
            url=CALENDAR_URL, username=CALENDAR_USER, password=CALENDAR_PASSWORD
        )

        calendar_path = f"{CALENDAR_URL}/{CALENDAR_USER}/{CALENDAR_ID}/"
        principal = client.principal()
        calendars = principal.calendars()

        calendar = next((c for c in calendars if str(c.url) == calendar_path), None)

        if not calendar:
            logger.warning(f"Could not find calendar at {calendar_path}")
            return {"upcoming": []}

        start = datetime.now(timezone.utc).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        end = datetime.now(timezone.utc) + timedelta(days=DAYS_AHEAD)
        todos = calendar.search(
            start=start,
            end=end,
            todo=True,
            expand=True,
            include_completed=True,
        )
        events = calendar.search(
            start=start,
            end=end,
            event=True,
            expand=True,
        )

    except Exception as e:
        logger.error(f"Error connecting to or retrieving tasks from CalDAV: {e}")
        return {"upcoming": []}

    upcoming: List[Dict[str, Any]] = []
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for todo in todos:
        try:
            vtodo = todo.vobject_instance.vtodo

            title = getattr(vtodo, "summary", None)
            due = getattr(vtodo, "due", None)
            completed = getattr(vtodo, "completed", None)
            if title:
                date_key = due.value.strftime("%Y%m%d")
                todo_object: Dict[str, Any] = {
                    "type": "todo",
                    "title": title.value if title else None,
                    "completed": True if completed else False,
                    "due": helpers.iso_to_time(due.value.isoformat()) if due else None,
                }

            upcoming.append(todo_object)
            if date_key not in grouped:
                grouped[date_key] = []
            grouped[date_key].append(todo_object)

        except Exception as e:
            logger.warning(f"Skipping a task due to processing error: {e}")
            continue

    for event in events:
        try:
            vevent = event.vobject_instance.vevent

            title = getattr(vevent, "summary", None)
            start = getattr(vevent, "dtstart", None)
            end = getattr(vevent, "dtend", None)

            if start and end:
                date_key = start.value.strftime("%Y%m%d")
                event_object: Dict[str, Any] = {
                    "type": "event",
                    "title": title.value if title else None,
                    "start": helpers.iso_to_time(start.value.isoformat())
                    if start
                    else None,
                    "end": helpers.iso_to_time(end.value.isoformat()) if end else None,
                }

            upcoming.append(event_object)
            if date_key not in grouped:
                grouped[date_key] = []
            grouped[date_key].append(event_object)

        except Exception as e:
            logger.warning(f"Skipping event due to processing error: {e}")
            continue

    return {
        "upcoming": grouped,
    }


def generate_countdowns() -> Dict[str, List[Dict]]:
    if not all([CALENDAR_URL, CALENDAR_USER, CALENDAR_PASSWORD, CALENDAR_ID]):
        logger.error("Missing environment variables required for CalDAV connection.")
        raise EnvironmentError(
            "CalDAV credentials are not fully set in the environment."
        )

    try:
        client = DAVClient(
            url=CALENDAR_URL, username=CALENDAR_USER, password=CALENDAR_PASSWORD
        )

        calendar_path = f"{CALENDAR_URL}/{CALENDAR_USER}/{CALENDAR_ID}/"
        principal = client.principal()
        calendars = principal.calendars()

        calendar = next((c for c in calendars if str(c.url) == calendar_path), None)

        if not calendar:
            logger.warning(f"Could not find calendar at {calendar_path}")
            return {"countdowns": None}

        now = datetime.now(timezone.utc)
        start = now
        end = datetime(now.year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        tag = "starred"
        search_term = "birthday"
        matches = []

        events = calendar.search(
            start=start,
            end=end,
            event=True,
        )

    except Exception as e:
        logger.error(f"Error connecting to or retrieving events from CalDAV: {e}")
        return {"countdowns": None}

    for event in events:
        try:
            vevent = event.vobject_instance.vevent

            title = getattr(vevent, "summary", None)
            start = getattr(vevent, "dtstart", None)
            end = getattr(vevent, "dtend", None)
            location = getattr(vevent, "location", None)
            categories = []

            if hasattr(vevent, "categories"):
                raw = vevent.categories.value
                if isinstance(raw, list):
                    categories = raw
                else:
                    categories = [c.strip() for c in str(raw).split(",")]

            if tag in categories or search_term.lower() in title.value.lower():
                matched_event: Dict[str, Any] = {
                    "type": "event",
                    "title": title.value if title else None,
                    "date": start.value.strftime("%Y-%m-%d"),
                    "in": helpers.calc_time_diff(
                        datetime.now(timezone.utc), parse(start.value.isoformat())
                    )
                    if start
                    else None,
                    "start": helpers.iso_to_time(start.value.isoformat())
                    if start
                    else None,
                    "end": helpers.iso_to_time(end.value.isoformat()) if end else None,
                    "location": location.value.replace("\n", ", ")
                    if location
                    else None,
                }
                matches.append(matched_event)

        except Exception as e:
            logger.warning(f"Skipping event due to processing error: {e}")
            continue

    sorted_countdowns = sorted(
        matches, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), reverse=False
    )

    return {"countdowns": sorted_countdowns}


@todos_bp.route("/api/calendar")
def get_todos():
    """
    Flask endpoint to retrieve events and todos from the CalDAV calendar.
    """
    try:
        data = fetch_from_calendar()
        return jsonify(data)
    except EnvironmentError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.critical(f"Unhandled error in get_todos: {e}", exc_info=True)
        return jsonify(
            {
                "error": "An internal server error occurred while connecting to the calendar."
            }
        ), 500


@todos_bp.route("/api/countdowns")
def get_countdowns():
    try:
        data = generate_countdowns()
        return jsonify(data)
    except EnvironmentError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.critical(f"Unhandled error in get_todos: {e}", exc_info=True)
        return jsonify(
            {
                "error": "An internal server error occurred while connecting to the calendar."
            }
        ), 500
