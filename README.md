# MCP Server for Voice-Controlled Scheduling

This Flask server acts as a secure and simplified interface (a Multi-turn Conversation Platform or MCP) between a voice agent (like one powered by Twilio and OpenAI) and the main `moving-scheduling-server`.

Its primary purpose is to expose a set of simple, high-level API endpoints that are easy for a Large Language Model (LLM) to use as "tools".

## Endpoints

- `GET /api/availability?date=YYYY-MM-DD`
  - Checks for available appointment slots on a given date.

- `POST /api/appointments`
  - Creates a new appointment. It handles the logic of finding or creating a customer before booking the appointment.

- `GET /api/appointments/by-phone/<phone_number>`
  - Retrieves all upcoming appointments for a customer based on their phone number.

- `DELETE /api/appointments/<appointment_id>`
  - Cancels an appointment.

## Setup and Running

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Server:**
    ```bash
    python app.py
    ```

    The server will run on port `5002` by default.

## Configuration

The server connects to the main `moving-scheduling-server`. The URL for this server is configured via an environment variable:

- `SCHEDULING_API_URL`: The base URL for the scheduling server API. Defaults to `http://localhost:5001/api`.
