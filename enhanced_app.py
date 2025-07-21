"""
Enhanced MCP Server for Voice-Controlled Moving Scheduling

This Flask server provides a comprehensive API for moving appointment scheduling,
designed specifically for integration with voice agents and LLM function calling.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional
from schemas import (
    AvailabilityRequest, AvailabilityResponse, CreateAppointmentRequest, 
    CreateAppointmentResponse, CustomerAppointmentsResponse, CancelAppointmentResponse,
    ServiceQuoteRequest, ServiceQuoteResponse, AppointmentSummary, LLM_TOOL_DEFINITIONS
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
SCHEDULING_API_URL = os.environ.get("SCHEDULING_API_URL", "http://localhost:5001/api")
DEFAULT_BUSINESS_HOURS = {"start": {"hour": 9, "minute": 0}, "end": {"hour": 17, "minute": 0}}
DEFAULT_APPOINTMENT_DURATION = 120  # minutes
BASE_HOURLY_RATE = 150.0  # Base rate per hour for moving services

def handle_api_error(error: Exception, context: str) -> tuple:
    """Centralized error handling for API calls"""
    logger.error(f"API Error in {context}: {str(error)}")
    return jsonify({"error": f"Service temporarily unavailable: {context}"}), 500

def validate_request_data(data: Dict[str, Any], required_fields: List[str]) -> Optional[tuple]:
    """Validate request data and return error response if invalid"""
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
    return None

@app.route('/api/tools', methods=['GET'])
def get_llm_tools():
    """
    Returns the tool definitions for LLM function calling integration.
    This endpoint helps the voice server understand what tools are available.
    """
    return jsonify({
        "tools": LLM_TOOL_DEFINITIONS,
        "description": "MCP tools for moving appointment scheduling",
        "version": "1.1.0"
    })

@app.route('/api/availability', methods=['GET'])
def check_availability():
    """
    Enhanced availability checking with better error handling and response format.
    """
    target_date_str = request.args.get('date')
    if not target_date_str:
        return jsonify({"error": "A 'date' query parameter is required in YYYY-MM-DD format."}), 400

    # Validate date format
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        
        # Check if date is in the past
        if target_date < datetime.now().date():
            return jsonify({"error": "Cannot check availability for past dates."}), 400
            
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    # Fetch existing appointments
    try:
        response = requests.get(
            f"{SCHEDULING_API_URL}/appointments", 
            params={"start_date": target_date_str, "end_date": target_date_str},
            timeout=10
        )
        response.raise_for_status()
        appointments = response.json()
    except requests.RequestException as e:
        return handle_api_error(e, "fetching appointments")

    # Calculate available slots
    business_hours = DEFAULT_BUSINESS_HOURS
    start_time = datetime.combine(target_date, datetime.min.time()).replace(
        hour=business_hours["start"]["hour"], 
        minute=business_hours["start"]["minute"]
    )
    end_time = datetime.combine(target_date, datetime.min.time()).replace(
        hour=business_hours["end"]["hour"], 
        minute=business_hours["end"]["minute"]
    )
    
    appointment_duration = timedelta(minutes=DEFAULT_APPOINTMENT_DURATION)
    
    # Create set of booked time slots
    booked_slots = set()
    for appt in appointments:
        try:
            appt_time = datetime.fromisoformat(f"{appt['appointment_date']}T{appt['appointment_time']}").time()
            booked_slots.add(appt_time)
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid appointment data: {appt}, error: {e}")

    # Generate available slots
    available_slots = []
    current_time = start_time
    while current_time < end_time:
        if current_time.time() not in booked_slots:
            available_slots.append(current_time.strftime('%H:%M'))
        current_time += appointment_duration

    response_data = AvailabilityResponse(
        date=target_date_str,
        available_slots=available_slots,
        business_hours={
            "start": f"{business_hours['start']['hour']:02d}:{business_hours['start']['minute']:02d}",
            "end": f"{business_hours['end']['hour']:02d}:{business_hours['end']['minute']:02d}"
        }
    )

    return jsonify(response_data.to_dict())

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    """
    Enhanced appointment creation with better validation and error handling.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must contain JSON data."}), 400

    # Validate required fields
    error_response = validate_request_data(data, [
        "customer_phone", "customer_name", "appointment_date", 
        "appointment_time", "origin_address", "destination_address"
    ])
    if error_response:
        return error_response

    # Create and validate request object
    try:
        appt_request = CreateAppointmentRequest(**data)
        validation_errors = appt_request.validate()
        if validation_errors:
            return jsonify({"error": "Validation failed", "details": validation_errors}), 400
    except TypeError as e:
        return jsonify({"error": f"Invalid request data: {str(e)}"}), 400

    # Find or create customer
    try:
        # Search for existing customer
        response = requests.get(f"{SCHEDULING_API_URL}/customers", timeout=10)
        response.raise_for_status()
        customers = response.json()
        customer = next((c for c in customers if c['phone'] == data['customer_phone']), None)

        if customer:
            customer_id = customer['id']
            logger.info(f"Found existing customer: {customer_id}")
        else:
            # Create new customer
            customer_data = {
                "name": data["customer_name"], 
                "phone": data["customer_phone"],
                "email": data.get("customer_email", "")
            }
            response = requests.post(f"{SCHEDULING_API_URL}/customers", json=customer_data, timeout=10)
            response.raise_for_status()
            customer_id = response.json()['id']
            logger.info(f"Created new customer: {customer_id}")
            
    except requests.RequestException as e:
        return handle_api_error(e, "managing customer data")

    # Create appointment
    try:
        appointment_data = {
            "customer_id": customer_id,
            "appointment_date": data["appointment_date"],
            "appointment_time": data["appointment_time"],
            "origin_address": data["origin_address"],
            "destination_address": data["destination_address"],
            "notes": data.get("notes", ""),
            "service_type": data.get("service_type", "residential_move"),
            "estimated_hours": data.get("estimated_hours", 2),
            "status": "scheduled"
        }
        
        response = requests.post(f"{SCHEDULING_API_URL}/appointments", json=appointment_data, timeout=10)
        response.raise_for_status()
        new_appointment = response.json()
        
        logger.info(f"Created appointment: {new_appointment['id']}")
        
    except requests.RequestException as e:
        return handle_api_error(e, "creating appointment")

    # Format response
    response_data = CreateAppointmentResponse(
        appointment_id=new_appointment['id'],
        customer_id=customer_id,
        status=new_appointment['status'],
        message=f"Appointment successfully scheduled for {data['customer_name']} on {data['appointment_date']} at {data['appointment_time']}.",
        appointment_details={
            "date": data["appointment_date"],
            "time": data["appointment_time"],
            "origin": data["origin_address"],
            "destination": data["destination_address"],
            "service_type": data.get("service_type", "residential_move")
        }
    )

    return jsonify(response_data.to_dict()), 201

@app.route('/api/appointments/by-phone/<string:phone_number>', methods=['GET'])
def get_appointments_by_phone(phone_number):
    """
    Enhanced customer appointment lookup with better formatting.
    """
    try:
        # Find customer by phone
        response = requests.get(f"{SCHEDULING_API_URL}/customers", timeout=10)
        response.raise_for_status()
        customers = response.json()
        customer = next((c for c in customers if c['phone'] == phone_number), None)

        if not customer:
            return jsonify({
                "customer_phone": phone_number,
                "customer_name": "Unknown",
                "appointments": [],
                "total_appointments": 0,
                "message": "No customer found with this phone number."
            })

        # Get customer appointments
        response = requests.get(f"{SCHEDULING_API_URL}/appointments", timeout=10)
        response.raise_for_status()
        all_appointments = response.json()
        
        # Filter and format appointments
        customer_appointments = [
            appt for appt in all_appointments 
            if appt['customer_id'] == customer['id'] 
            and datetime.fromisoformat(appt['appointment_date']).date() >= datetime.today().date()
        ]
        
        formatted_appointments = [
            AppointmentSummary(
                appointment_id=appt['id'],
                appointment_date=appt['appointment_date'],
                appointment_time=appt['appointment_time'],
                status=appt['status'],
                origin_address=appt['origin_address'],
                destination_address=appt['destination_address'],
                service_type=appt.get('service_type', 'residential_move'),
                estimated_hours=appt.get('estimated_hours', 2)
            ) for appt in customer_appointments
        ]

        response_data = CustomerAppointmentsResponse(
            customer_phone=phone_number,
            customer_name=customer['name'],
            appointments=formatted_appointments,
            total_appointments=len(formatted_appointments)
        )

        return jsonify(response_data.to_dict())

    except requests.RequestException as e:
        return handle_api_error(e, "retrieving customer appointments")

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
def cancel_appointment(appointment_id):
    """
    Enhanced appointment cancellation with better response format.
    """
    try:
        response = requests.delete(f"{SCHEDULING_API_URL}/appointments/{appointment_id}", timeout=10)
        
        if response.status_code == 404:
            return jsonify({"error": "Appointment not found."}), 404
        
        response.raise_for_status()
        
        response_data = CancelAppointmentResponse(
            appointment_id=appointment_id,
            status="cancelled",
            message=f"Appointment {appointment_id} has been successfully cancelled.",
            cancelled_at=datetime.now().isoformat()
        )
        
        logger.info(f"Cancelled appointment: {appointment_id}")
        return jsonify(response_data.to_dict())
        
    except requests.RequestException as e:
        return handle_api_error(e, "cancelling appointment")

@app.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
def modify_appointment(appointment_id):
    """
    New endpoint to modify existing appointments.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must contain JSON data."}), 400

    try:
        # Get existing appointment
        response = requests.get(f"{SCHEDULING_API_URL}/appointments/{appointment_id}", timeout=10)
        if response.status_code == 404:
            return jsonify({"error": "Appointment not found."}), 404
        response.raise_for_status()
        
        existing_appointment = response.json()
        
        # Update fields
        update_data = {}
        if 'new_date' in data:
            update_data['appointment_date'] = data['new_date']
        if 'new_time' in data:
            update_data['appointment_time'] = data['new_time']
        if 'new_notes' in data:
            update_data['notes'] = data['new_notes']
        
        if not update_data:
            return jsonify({"error": "No valid fields to update provided."}), 400
        
        # Apply updates
        response = requests.put(
            f"{SCHEDULING_API_URL}/appointments/{appointment_id}", 
            json=update_data, 
            timeout=10
        )
        response.raise_for_status()
        updated_appointment = response.json()
        
        logger.info(f"Modified appointment: {appointment_id}")
        
        return jsonify({
            "appointment_id": appointment_id,
            "status": "modified",
            "message": f"Appointment {appointment_id} has been successfully updated.",
            "updated_fields": list(update_data.keys()),
            "appointment_details": updated_appointment
        })
        
    except requests.RequestException as e:
        return handle_api_error(e, "modifying appointment")

@app.route('/api/quotes', methods=['POST'])
def get_service_quote():
    """
    New endpoint to provide service quotes based on move details.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must contain JSON data."}), 400

    try:
        quote_request = ServiceQuoteRequest(**data)
        validation_errors = quote_request.validate()
        if validation_errors:
            return jsonify({"error": "Validation failed", "details": validation_errors}), 400
    except TypeError as e:
        return jsonify({"error": f"Invalid request data: {str(e)}"}), 400

    # Calculate quote (simplified logic - in real implementation, this would be more sophisticated)
    service_multipliers = {
        "residential_move": 1.0,
        "commercial_move": 1.3,
        "packing_only": 0.7,
        "storage": 0.5
    }
    
    base_hours = quote_request.estimated_hours or 4
    multiplier = service_multipliers.get(quote_request.service_type, 1.0)
    base_rate = BASE_HOURLY_RATE * base_hours * multiplier
    
    # Add fees for special items
    special_items_fee = 0.0
    if quote_request.special_items:
        special_items_fee = len(quote_request.special_items) * 50.0  # $50 per special item
    
    # Simple travel fee calculation (would be more sophisticated in real implementation)
    travel_fee = 25.0  # Flat travel fee
    
    estimated_total = base_rate + special_items_fee + travel_fee
    
    response_data = ServiceQuoteResponse(
        base_rate=base_rate,
        estimated_hours=base_hours,
        estimated_total=estimated_total,
        service_type=quote_request.service_type,
        special_items_fee=special_items_fee,
        travel_fee=travel_fee,
        breakdown={
            "labor": base_rate,
            "special_items": special_items_fee,
            "travel": travel_fee
        }
    )
    
    logger.info(f"Generated quote: ${estimated_total:.2f} for {quote_request.service_type}")
    return jsonify(response_data.to_dict())

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test connection to scheduling API
        response = requests.get(f"{SCHEDULING_API_URL}/health", timeout=5)
        scheduling_api_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        scheduling_api_status = "unreachable"
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.1.0",
        "dependencies": {
            "scheduling_api": scheduling_api_status
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("Starting Enhanced MCP Server v1.1.0")
    app.run(host='0.0.0.0', port=5002, debug=False)

