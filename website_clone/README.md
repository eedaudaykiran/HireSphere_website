# Job Portal (Naukri Clone)

A full-stack Django job portal with employer and candidate dashboards.

## Tech Stack
- Python 3.x / Django 5.2
- PostgreSQL
- HTML/CSS/JavaScript

## Features
- Dual-role system (Employer / Candidate)
- 20+ job category pages with advanced filtering
- Employer dashboard with application management
- Interview scheduling

## Setup
1. Clone the repo
2. Create virtualenv: `python -m venv venv`
3. Install deps: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in values
5. Run migrations: `python manage.py migrate`
6. Run server: `python manage.py runserver`

## Run Tests
python manage.py test core