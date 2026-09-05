# College Event Management System

A Flask-based web app for managing college events, student registrations, and admin verification, with QR-code based admit cards.

## Features
- Admin and student login/registration
- Event creation and management
- Student registration for events
- QR code generation for admit cards
- Leaderboard and batch/student views

## Setup

1. Clone the repo and enter the project folder:
   ```bash
   git clone <your-repo-url>
   cd em-4
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set a secret key (recommended):
   ```bash
   export SECRET_KEY="your-random-secret-key"   # on Windows: set SECRET_KEY=your-random-secret-key
   ```

4. Run the app:
   ```bash
   python app.py
   ```

The app will create `instance/collegeevents.db` automatically on first run (SQLite).

## Notes
- The database file is not tracked in git (see `.gitignore`). Each environment generates its own local DB.
- Update `SECRET_KEY` before deploying to production.
