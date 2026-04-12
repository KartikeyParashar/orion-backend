# ORION Backend

This is the backend for the ORION (Ordering, Replenishment, and Inventory Optimization Network) project. It is built using Django.

## Prerequisites

- Python 3.9+
- pip

## Setup Instructions

1. **Create a Virtual Environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate the Virtual Environment:**
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: If requirements.txt is missing, install Django and other necessary packages)*

4. **Database Migrations:**
   ```bash
   python manage.py migrate
   ```

## Running the Server

To start the development server, run:
```bash
python manage.py runserver
```

The server will be available at `http://127.0.0.1:8000/`.

## API Endpoints

- `/admin/` - Django Administration
- `/api/` - Backend API services (as configured in `core/urls.py`)
