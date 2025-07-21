"""
API Schemas for Moving Scheduling MCP Server

This module defines the input/output schemas for all MCP API endpoints
to ensure consistent data validation and clear documentation for LLM tool integration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass, asdict
from enum import Enum

class AppointmentStatus(Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class AvailabilityRequest:
    """Request schema for checking appointment availability"""
    date: str  # YYYY-MM-DD format
    
    def validate(self) -> Dict[str, Any]:
        """Validate the request and return errors if any"""
        errors = {}
        try:
            datetime.strptime(self.date, '%Y-%m-%d')
        except ValueError:
            errors['date'] = 'Invalid date format. Use YYYY-MM-DD'
        return errors

@dataclass
class AvailabilityResponse:
    """Response schema for availability check"""
    date: str
    available_slots: List[str]  # List of time slots in HH:MM format
    business_hours: Dict[str, str]  # start and end times
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CreateAppointmentRequest:
    """Request schema for creating a new appointment"""
    customer_phone: str
    customer_name: str
    appointment_date: str  # YYYY-MM-DD format
    appointment_time: str  # HH:MM format
    origin_address: str
    destination_address: str
    notes: Optional[str] = ""
    service_type: Optional[str] = "residential_move"
    estimated_hours: Optional[int] = 2
    
    def validate(self) -> Dict[str, Any]:
        """Validate the request and return errors if any"""
        errors = {}
        
        # Validate required fields
        required_fields = ['customer_phone', 'customer_name', 'appointment_date', 
                          'appointment_time', 'origin_address', 'destination_address']
        for field in required_fields:
            if not getattr(self, field):
                errors[field] = f'{field} is required'
        
        # Validate date format
        try:
            datetime.strptime(self.appointment_date, '%Y-%m-%d')
        except ValueError:
            errors['appointment_date'] = 'Invalid date format. Use YYYY-MM-DD'
        
        # Validate time format
        try:
            datetime.strptime(self.appointment_time, '%H:%M')
        except ValueError:
            errors['appointment_time'] = 'Invalid time format. Use HH:MM'
        
        # Validate phone format (basic check)
        if self.customer_phone and not self.customer_phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', '').isdigit():
            errors['customer_phone'] = 'Invalid phone number format'
        
        return errors

@dataclass
class CreateAppointmentResponse:
    """Response schema for appointment creation"""
    appointment_id: int
    customer_id: int
    status: str
    message: str
    appointment_details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AppointmentSummary:
    """Schema for appointment summary information"""
    appointment_id: int
    appointment_date: str
    appointment_time: str
    status: str
    origin_address: str
    destination_address: str
    service_type: Optional[str] = None
    estimated_hours: Optional[int] = None

@dataclass
class CustomerAppointmentsResponse:
    """Response schema for customer appointments lookup"""
    customer_phone: str
    customer_name: str
    appointments: List[AppointmentSummary]
    total_appointments: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'customer_phone': self.customer_phone,
            'customer_name': self.customer_name,
            'appointments': [asdict(appt) for appt in self.appointments],
            'total_appointments': self.total_appointments
        }

@dataclass
class CancelAppointmentResponse:
    """Response schema for appointment cancellation"""
    appointment_id: int
    status: str
    message: str
    cancelled_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ServiceQuoteRequest:
    """Request schema for getting service quotes"""
    origin_address: str
    destination_address: str
    service_type: str = "residential_move"
    estimated_hours: Optional[int] = None
    special_items: Optional[List[str]] = None
    
    def validate(self) -> Dict[str, Any]:
        """Validate the request and return errors if any"""
        errors = {}
        
        if not self.origin_address:
            errors['origin_address'] = 'Origin address is required'
        if not self.destination_address:
            errors['destination_address'] = 'Destination address is required'
        
        valid_service_types = ['residential_move', 'commercial_move', 'packing_only', 'storage']
        if self.service_type not in valid_service_types:
            errors['service_type'] = f'Service type must be one of: {", ".join(valid_service_types)}'
        
        return errors

@dataclass
class ServiceQuoteResponse:
    """Response schema for service quotes"""
    base_rate: float
    estimated_hours: int
    estimated_total: float
    service_type: str
    special_items_fee: float
    travel_fee: float
    breakdown: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# LLM Tool Definitions for OpenAI Function Calling
LLM_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "check_appointment_availability",
            "description": "Check available appointment slots for a specific date. Returns list of available time slots during business hours.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to check availability for in YYYY-MM-DD format (e.g., '2024-03-15')"
                    }
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "create_appointment",
            "description": "Schedule a new moving appointment for a customer. Creates customer record if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer's phone number for contact and identification"
                    },
                    "customer_name": {
                        "type": "string", 
                        "description": "Customer's full name"
                    },
                    "appointment_date": {
                        "type": "string",
                        "description": "Date for the appointment in YYYY-MM-DD format"
                    },
                    "appointment_time": {
                        "type": "string",
                        "description": "Time for the appointment in HH:MM format (24-hour)"
                    },
                    "origin_address": {
                        "type": "string",
                        "description": "Address where items will be picked up from"
                    },
                    "destination_address": {
                        "type": "string", 
                        "description": "Address where items will be delivered to"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes or special instructions for the move"
                    },
                    "service_type": {
                        "type": "string",
                        "description": "Type of moving service",
                        "enum": ["residential_move", "commercial_move", "packing_only", "storage"]
                    },
                    "estimated_hours": {
                        "type": "integer",
                        "description": "Estimated duration of the move in hours"
                    }
                },
                "required": ["customer_phone", "customer_name", "appointment_date", "appointment_time", "origin_address", "destination_address"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_appointments",
            "description": "Retrieve all upcoming appointments for a customer using their phone number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "Customer's phone number to look up appointments"
                    }
                },
                "required": ["phone_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel an existing appointment by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "Unique ID of the appointment to cancel"
                    }
                },
                "required": ["appointment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_service_quote",
            "description": "Get an estimated quote for moving services based on addresses and service type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_address": {
                        "type": "string",
                        "description": "Address where items will be picked up from"
                    },
                    "destination_address": {
                        "type": "string",
                        "description": "Address where items will be delivered to"
                    },
                    "service_type": {
                        "type": "string",
                        "description": "Type of moving service requested",
                        "enum": ["residential_move", "commercial_move", "packing_only", "storage"]
                    },
                    "estimated_hours": {
                        "type": "integer",
                        "description": "Estimated duration of the move in hours"
                    },
                    "special_items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of special items that require extra care (piano, artwork, etc.)"
                    }
                },
                "required": ["origin_address", "destination_address"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "modify_appointment",
            "description": "Modify an existing appointment's date, time, or other details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "Unique ID of the appointment to modify"
                    },
                    "new_date": {
                        "type": "string",
                        "description": "New date for the appointment in YYYY-MM-DD format (optional)"
                    },
                    "new_time": {
                        "type": "string",
                        "description": "New time for the appointment in HH:MM format (optional)"
                    },
                    "new_notes": {
                        "type": "string",
                        "description": "Updated notes or special instructions (optional)"
                    }
                },
                "required": ["appointment_id"]
            }
        }
    }
]

