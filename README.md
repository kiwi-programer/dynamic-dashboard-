# Dynamic Dashboard

FastAPI + Jinja2 dashboard with touch-friendly subpages for:
- Notes
- Reminders
- Alarms
- Timers
- Quick Links
- Schoology assignments and grades

Data is stored locally in SQLite (`data/dashboard.db`) to keep memory and CPU usage low for Raspberry Pi.

## Quick Start

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

3. Open:

```text
http://localhost:8000/dashboard
```

## Schoology Setup

Use the `Schoology` page to save:
- Domain (example: `app.schoology.com`)
- API Key
- API Secret
- Access Token + Token Secret (if your app requires them)
- Section/Course ID

Once configured, the Schoology page will pull:
- Assignments (title, due date, description, quick link)
- Current grade data (when available)
- Grade impact estimate using your expected score

## Raspberry Pi (1GB RAM) Optimization

- Keep one process:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --no-access-log
```

- Avoid `--reload` in production.
- Use wired ethernet when possible.
- Use a lightweight browser in kiosk mode for the 7-inch touchscreen.
- The UI uses low-overhead CSS/JS and no frontend build step.

## Project Layout

```
app/
	main.py
	schoology.py
	storage.py
templates/
	base.html
	dashboard.html
	notes.html
	reminders.html
	alarms.html
	timers.html
	quick_links.html
	schoology.html
static/
	styles.css
	app.js
data/
	dashboard.db (created at runtime)
```