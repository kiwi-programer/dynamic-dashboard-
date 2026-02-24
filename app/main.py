from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .storage import (
    add_alarm,
    add_note,
    add_quick_link,
    add_reminder,
    add_timer,
    delete_alarm,
    delete_note,
    delete_quick_link,
    delete_reminder,
    delete_timer,
    get_counts,
    get_settings,
    init_db,
    list_alarms,
    list_notes,
    list_quick_links,
    list_reminders,
    list_timers,
    set_setting,
    toggle_reminder,
)
from .schoology import SchoologyClient


BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Dynamic Dashboard", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
def startup_event() -> None:
    init_db()


def render(
    request: Request,
    template_name: str,
    context: dict[str, Any],
    status_code: int = 200,
) -> HTMLResponse:
    base_context = {
        "request": request,
        "now": datetime.now(),
    }
    base_context.update(context)
    return templates.TemplateResponse(template_name, base_context, status_code=status_code)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    reminders = list_reminders(limit=5)
    notes = list_notes(limit=5)
    quick_links = list_quick_links(limit=8)
    counts = get_counts()

    schoology_status = "Not connected"
    schoology_settings = get_settings(prefix="schoology_")
    if schoology_settings.get("schoology_domain") and schoology_settings.get("schoology_key"):
        schoology_status = "Configured"

    return render(
        request,
        "dashboard.html",
        {
            "title": "Dashboard",
            "reminders": reminders,
            "notes": notes,
            "quick_links": quick_links,
            "counts": counts,
            "schoology_status": schoology_status,
        },
    )


@app.get("/notes", response_class=HTMLResponse)
def notes_page(request: Request) -> HTMLResponse:
    return render(
        request,
        "notes.html",
        {
            "title": "Notes",
            "notes": list_notes(),
        },
    )


@app.post("/notes/add")
def notes_add(title: str = Form(...), content: str = Form("")) -> RedirectResponse:
    add_note(title=title.strip(), content=content.strip())
    return RedirectResponse(url="/notes", status_code=303)


@app.post("/notes/{note_id}/delete")
def notes_delete(note_id: int) -> RedirectResponse:
    delete_note(note_id)
    return RedirectResponse(url="/notes", status_code=303)


@app.get("/reminders", response_class=HTMLResponse)
def reminders_page(request: Request) -> HTMLResponse:
    return render(
        request,
        "reminders.html",
        {
            "title": "Reminders",
            "reminders": list_reminders(),
        },
    )


@app.post("/reminders/add")
def reminders_add(text: str = Form(...), due_at: str = Form("")) -> RedirectResponse:
    add_reminder(text=text.strip(), due_at=due_at.strip() or None)
    return RedirectResponse(url="/reminders", status_code=303)


@app.post("/reminders/{reminder_id}/toggle")
def reminders_toggle(reminder_id: int) -> RedirectResponse:
    toggle_reminder(reminder_id)
    return RedirectResponse(url="/reminders", status_code=303)


@app.post("/reminders/{reminder_id}/delete")
def reminders_delete(reminder_id: int) -> RedirectResponse:
    delete_reminder(reminder_id)
    return RedirectResponse(url="/reminders", status_code=303)


@app.get("/alarms", response_class=HTMLResponse)
def alarms_page(request: Request) -> HTMLResponse:
    return render(
        request,
        "alarms.html",
        {
            "title": "Alarms",
            "alarms": list_alarms(),
        },
    )


@app.post("/alarms/add")
def alarms_add(label: str = Form(...), time_of_day: str = Form(...)) -> RedirectResponse:
    add_alarm(label=label.strip(), time_of_day=time_of_day.strip())
    return RedirectResponse(url="/alarms", status_code=303)


@app.post("/alarms/{alarm_id}/delete")
def alarms_delete(alarm_id: int) -> RedirectResponse:
    delete_alarm(alarm_id)
    return RedirectResponse(url="/alarms", status_code=303)


@app.get("/timers", response_class=HTMLResponse)
def timers_page(request: Request) -> HTMLResponse:
    return render(
        request,
        "timers.html",
        {
            "title": "Timers",
            "timers": list_timers(),
        },
    )


@app.post("/timers/add")
def timers_add(label: str = Form(...), seconds: int = Form(...)) -> RedirectResponse:
    add_timer(label=label.strip(), seconds=max(1, min(seconds, 86400)))
    return RedirectResponse(url="/timers", status_code=303)


@app.post("/timers/{timer_id}/delete")
def timers_delete(timer_id: int) -> RedirectResponse:
    delete_timer(timer_id)
    return RedirectResponse(url="/timers", status_code=303)


@app.get("/quick-links", response_class=HTMLResponse)
def quick_links_page(request: Request) -> HTMLResponse:
    return render(
        request,
        "quick_links.html",
        {
            "title": "Quick Links",
            "quick_links": list_quick_links(),
        },
    )


@app.post("/quick-links/add")
def quick_links_add(title: str = Form(...), url: str = Form(...)) -> RedirectResponse:
    add_quick_link(title=title.strip(), url=url.strip())
    return RedirectResponse(url="/quick-links", status_code=303)


@app.post("/quick-links/{link_id}/delete")
def quick_links_delete(link_id: int) -> RedirectResponse:
    delete_quick_link(link_id)
    return RedirectResponse(url="/quick-links", status_code=303)


@app.get("/schoology", response_class=HTMLResponse)
def schoology_page(request: Request, message: str = "", error: str = "") -> HTMLResponse:
    settings = get_settings(prefix="schoology_")
    settings.setdefault("schoology_domain", "")
    settings.setdefault("schoology_key", "")
    settings.setdefault("schoology_secret", "")
    settings.setdefault("schoology_token", "")
    settings.setdefault("schoology_token_secret", "")
    settings.setdefault("schoology_section_id", "")

    assignments: list[dict[str, Any]] = []
    grades: dict[str, Any] = {}
    connect_error = ""

    if settings["schoology_domain"] and settings["schoology_key"] and settings["schoology_secret"]:
        try:
            client = SchoologyClient(
                domain=settings["schoology_domain"],
                key=settings["schoology_key"],
                secret=settings["schoology_secret"],
                token=settings["schoology_token"],
                token_secret=settings["schoology_token_secret"],
            )
            section_id = settings.get("schoology_section_id", "")
            if section_id:
                assignments = client.fetch_assignments(section_id=section_id)
                grades = client.fetch_grades(section_id=section_id)
        except Exception as exc:
            connect_error = str(exc)

    return render(
        request,
        "schoology.html",
        {
            "title": "Schoology",
            "settings": settings,
            "assignments": assignments,
            "grades": grades,
            "message": message,
            "error": error or connect_error,
        },
    )


@app.post("/schoology/settings")
def schoology_settings_save(
    domain: str = Form(""),
    key: str = Form(""),
    secret: str = Form(""),
    token: str = Form(""),
    token_secret: str = Form(""),
    section_id: str = Form(""),
) -> RedirectResponse:
    set_setting("schoology_domain", domain.strip())
    set_setting("schoology_key", key.strip())
    set_setting("schoology_secret", secret.strip())
    set_setting("schoology_token", token.strip())
    set_setting("schoology_token_secret", token_secret.strip())
    set_setting("schoology_section_id", section_id.strip())
    return RedirectResponse(url="/schoology?message=Saved", status_code=303)
