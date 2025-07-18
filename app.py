
from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuration for the moving-scheduling-server API
SCHEDULING_API_URL = os.environ.get("SCHEDULING_API_URL", "http://localhost:5001/api")

def get_business_hours():
    """Defines the business hours."""
    return {
        "start": {"hour": 9, "minute": 0},
        "end": {"hour": 17, "minute": 0}
    }

def get_appointment_duration():
    """Defines the assumed duration of an appointment in minutes."""
    return 120  # 2 hours

@app.route('/api/availability', methods=['GET'])
def check_availability():
    """
    Checks available appointment slots for a given date.
    Query Params:
        - date (str): The date to check in YYYY-MM-DD format.
    """
    target_date_str = request.args.get('date')
    if not target_date_str:
        return jsonify({"error": "A 'date' query parameter is required."}), 400

    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    # Fetch existing appointments for that day
    try:
        response = requests.get(f"{SCHEDULING_API_URL}/appointments", params={"start_date": target_date_str, "end_date": target_date_str})
        response.raise_for_status()
        appointments = response.json()
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to connect to scheduling service: {e}"}), 500

    # Calculate available slots
    business_hours = get_business_hours()
    start_time = datetime.combine(target_date, datetime.min.time()).replace(hour=business_hours["start"]["hour"], minute=business_hours["start"]["minute"])
    end_time = datetime.combine(target_date, datetime.min.time()).replace(hour=business_hours["end"]["hour"], minute=business_hours["end"]["minute"])
    
    appointment_duration = timedelta(minutes=get_appointment_duration())
    
    # Create a set of booked time slots for quick lookup
    booked_slots = set()
    for appt in appointments:
        appt_time = datetime.fromisoformat(f"{appt['appointment_date']}T{appt['appointment_time']}").time()
        booked_slots.add(appt_time)

    available_slots = []
    current_time = start_time
    while current_time < end_time:
        if current_time.time() not in booked_slots:
            available_slots.append(current_time.strftime('%H:%M'))
        current_time += appointment_duration

    return jsonify({"available_slots": available_slots})

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    """
    Creates a new appointment.
    """
    data = request.get_json()
    required_fields = ["customer_phone", "customer_name", "appointment_date", "appointment_time", "origin_address", "destination_address"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields."}), 400

    # 1. Find or create the customer
    try:
        # Search for customer by phone
        response = requests.get(f"{SCHEDULING_API_URL}/customers")
        response.raise_for_status()
        customers = response.json()
        customer = next((c for c in customers if c['phone'] == data['customer_phone']), None)

        if customer:
            customer_id = customer['id']
        else:
            # Create a new customer
            customer_data = {"name": data["customer_name"], "phone": data["customer_phone"]}
            response = requests.post(f"{SCHEDULING_API_URL}/customers", json=customer_data)
            response.raise_for_status()
            customer_id = response.json()['id']
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to manage customer data: {e}"}), 500

    # 2. Create the appointment
    try:
        appointment_data = {
            "customer_id": customer_id,
            "appointment_date": data["appointment_date"],
            "appointment_time": data["appointment_time"],
            "origin_address": data["origin_address"],
            "destination_address": data["destination_address"],
            "notes": data.get("notes", ""),
            "status": "scheduled"
        }
        response = requests.post(f"{SCHEDULING_API_URL}/appointments", json=appointment_data)
        response.raise_for_status()
        new_appointment = response.json()
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to create appointment: {e}"}), 500

    return jsonify({
        "appointment_id": new_appointment['id'],
        "customer_id": customer_id,
        "status": new_appointment['status'],
        "message": f"Appointment successfully scheduled for {data['customer_name']} on {data['appointment_date']} at {data['appointment_time']}."
    }), 201

@app.route('/api/appointments/by-phone/<string:phone_number>', methods=['GET'])
def get_appointments_by_phone(phone_number):
    """
    Gets all appointments for a given phone number.
    """
    # 1. Find the customer by phone
    try:
        response = requests.get(f"{SCHEDULING_API_URL}/customers")
        response.raise_for_status()
        customers = response.json()
        customer = next((c for c in customers if c['phone'] == phone_number), None)

        if not customer:
            return jsonify({"appointments": []}) # No customer, so no appointments
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to find customer: {e}"}), 500

    # 2. Get all appointments for that customer
    try:
        response = requests.get(f"{SCHEDULING_API_URL}/appointments")
        response.raise_for_status()
        all_appointments = response.json()
        
        customer_appointments = [
            appt for appt in all_appointments 
            if appt['customer_id'] == customer['id'] and datetime.fromisoformat(appt['appointment_date']).date() >= datetime.today().date()
        ]
        
        # Format for the response
        formatted_appointments = [{
            "appointment_id": appt['id'],
            "appointment_date": appt['appointment_date'],
            "appointment_time": appt['appointment_time'],
            "status": appt['status'],
            "origin_address": appt['origin_address']
        } for appt in customer_appointments]

    except requests.RequestException as e:
        return jsonify({"error": f"Failed to retrieve appointments: {e}"}), 500

    return jsonify({"appointments": formatted_appointments})

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
def cancel_appointment(appointment_id):
    """
    Cancels an appointment by its ID.
    """
    try:
        response = requests.delete(f"{SCHEDULING_API_URL}/appointments/{appointment_id}")
        
        if response.status_code == 404:
            return jsonify({"error": "Appointment not found."}), 404
        
        response.raise_for_status() # Raise for other errors (e.g., 500)
        
        return jsonify({"message": f"Appointment {appointment_id} has been successfully cancelled."}), 200
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to cancel appointment: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
