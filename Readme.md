# Equipment Maintenance System

A simple Python web application for tracking equipment, maintenance schedules, and service history.

## Features

- Add, update, and delete equipment records
- Record maintenance history for each item
- View dashboard totals and service alerts
- Search and filter by status, type, serial number, or location
- Simple browser-based interface for staff

## Tech Stack

- Python 3
- Flask
- SQLite
- HTML, CSS, and vanilla JavaScript

## Run Locally

1. Create a virtual environment:
   `python -m venv .venv`
2. Activate it:
   `.\.venv\Scripts\Activate.ps1`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Start the server:
   `python app.py`
5. Open:
   `http://127.0.0.1:5000`

## API Endpoints

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/equipment`
- `POST /api/equipment`
- `PUT /api/equipment/<id>`
- `DELETE /api/equipment/<id>`
- `GET /api/maintenance`
- `POST /api/maintenance`
- `DELETE /api/maintenance/<id>`

## Notes

- The SQLite database file is created automatically as `maintenance.db`
- Service alerts highlight equipment due within the next 14 days
- This repo was scaffolded with OpenAI Codex assistance
