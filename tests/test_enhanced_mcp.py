"""
Test suite for Enhanced MCP Server

Tests all API endpoints and tool integrations to ensure reliability
for voice agent integration.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_app import app
from schemas import LLM_TOOL_DEFINITIONS

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_scheduling_api():
    """Mock responses for the scheduling API."""
    return {
        'customers': [
            {'id': 1, 'name': 'John Doe', 'phone': '555-1234', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'phone': '555-5678', 'email': 'jane@example.com'}
        ],
        'appointments': [
            {
                'id': 1,
                'customer_id': 1,
                'appointment_date': '2024-03-15',
                'appointment_time': '10:00',
                'origin_address': '123 Main St',
                'destination_address': '456 Oak Ave',
                'status': 'scheduled',
                'service_type': 'residential_move',
                'estimated_hours': 3,
                'notes': 'Handle with care'
            }
        ]
    }

class TestToolDefinitions:
    """Test LLM tool definitions and metadata endpoints."""
    
    def test_get_llm_tools(self, client):
        """Test that tool definitions are properly returned."""
        response = client.get('/api/tools')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'tools' in data
        assert 'description' in data
        assert 'version' in data
        
        # Verify we have the expected number of tools
        assert len(data['tools']) == 6
        
        # Verify tool structure
        for tool in data['tools']:
            assert 'type' in tool
            assert tool['type'] == 'function'
            assert 'function' in tool
            assert 'name' in tool['function']
            assert 'description' in tool['function']
            assert 'parameters' in tool['function']

class TestAvailabilityAPI:
    """Test appointment availability checking."""
    
    @patch('enhanced_app.requests.get')
    def test_check_availability_success(self, mock_get, client, mock_scheduling_api):
        """Test successful availability check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_scheduling_api['appointments']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = client.get(f'/api/availability?date={tomorrow}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'available_slots' in data
        assert 'business_hours' in data
        assert 'date' in data
        assert data['date'] == tomorrow
    
    def test_check_availability_missing_date(self, client):
        """Test availability check without date parameter."""
        response = client.get('/api/availability')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'date' in data['error'].lower()
    
    def test_check_availability_invalid_date(self, client):
        """Test availability check with invalid date format."""
        response = client.get('/api/availability?date=invalid-date')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'format' in data['error'].lower()
    
    def test_check_availability_past_date(self, client):
        """Test availability check for past date."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = client.get(f'/api/availability?date={yesterday}')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'past' in data['error'].lower()

class TestAppointmentCreation:
    """Test appointment creation functionality."""
    
    @patch('enhanced_app.requests.post')
    @patch('enhanced_app.requests.get')
    def test_create_appointment_new_customer(self, mock_get, mock_post, client, mock_scheduling_api):
        """Test creating appointment for new customer."""
        # Mock customer lookup (empty result)
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response
        
        # Mock customer creation and appointment creation
        mock_post_responses = [
            Mock(status_code=201, json=lambda: {'id': 3}),  # Customer creation
            Mock(status_code=201, json=lambda: {'id': 2, 'status': 'scheduled'})  # Appointment creation
        ]
        mock_post.side_effect = mock_post_responses
        for response in mock_post_responses:
            response.raise_for_status.return_value = None
        
        appointment_data = {
            "customer_phone": "555-9999",
            "customer_name": "New Customer",
            "appointment_date": "2024-03-20",
            "appointment_time": "14:00",
            "origin_address": "789 Pine St",
            "destination_address": "321 Elm Ave",
            "notes": "Test appointment"
        }
        
        response = client.post('/api/appointments', 
                             data=json.dumps(appointment_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'appointment_id' in data
        assert 'customer_id' in data
        assert 'message' in data
        assert data['status'] == 'scheduled'
    
    def test_create_appointment_missing_fields(self, client):
        """Test appointment creation with missing required fields."""
        incomplete_data = {
            "customer_phone": "555-1234",
            "customer_name": "Test User"
            # Missing required fields
        }
        
        response = client.post('/api/appointments',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_appointment_invalid_date(self, client):
        """Test appointment creation with invalid date format."""
        invalid_data = {
            "customer_phone": "555-1234",
            "customer_name": "Test User",
            "appointment_date": "invalid-date",
            "appointment_time": "14:00",
            "origin_address": "123 Test St",
            "destination_address": "456 Test Ave"
        }
        
        response = client.post('/api/appointments',
                             data=json.dumps(invalid_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

class TestCustomerAppointments:
    """Test customer appointment lookup functionality."""
    
    @patch('enhanced_app.requests.get')
    def test_get_appointments_by_phone_success(self, mock_get, client, mock_scheduling_api):
        """Test successful customer appointment lookup."""
        mock_responses = [
            Mock(status_code=200, json=lambda: mock_scheduling_api['customers']),
            Mock(status_code=200, json=lambda: mock_scheduling_api['appointments'])
        ]
        mock_get.side_effect = mock_responses
        for response in mock_responses:
            response.raise_for_status.return_value = None
        
        response = client.get('/api/appointments/by-phone/555-1234')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'customer_phone' in data
        assert 'customer_name' in data
        assert 'appointments' in data
        assert 'total_appointments' in data
        assert data['customer_phone'] == '555-1234'
    
    @patch('enhanced_app.requests.get')
    def test_get_appointments_customer_not_found(self, mock_get, client):
        """Test appointment lookup for non-existent customer."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []  # No customers found
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        response = client.get('/api/appointments/by-phone/555-0000')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_appointments'] == 0
        assert 'No customer found' in data['message']

class TestAppointmentCancellation:
    """Test appointment cancellation functionality."""
    
    @patch('enhanced_app.requests.delete')
    def test_cancel_appointment_success(self, mock_delete, client):
        """Test successful appointment cancellation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response
        
        response = client.delete('/api/appointments/1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'appointment_id' in data
        assert 'status' in data
        assert 'message' in data
        assert data['appointment_id'] == 1
        assert data['status'] == 'cancelled'
    
    @patch('enhanced_app.requests.delete')
    def test_cancel_appointment_not_found(self, mock_delete, client):
        """Test cancellation of non-existent appointment."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_delete.return_value = mock_response
        
        response = client.delete('/api/appointments/999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()

class TestServiceQuotes:
    """Test service quote functionality."""
    
    def test_get_service_quote_success(self, client):
        """Test successful quote generation."""
        quote_data = {
            "origin_address": "123 Main St",
            "destination_address": "456 Oak Ave",
            "service_type": "residential_move",
            "estimated_hours": 4,
            "special_items": ["piano", "artwork"]
        }
        
        response = client.post('/api/quotes',
                             data=json.dumps(quote_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'estimated_total' in data
        assert 'base_rate' in data
        assert 'special_items_fee' in data
        assert 'breakdown' in data
        assert data['service_type'] == 'residential_move'
        assert data['estimated_hours'] == 4
    
    def test_get_service_quote_missing_fields(self, client):
        """Test quote generation with missing required fields."""
        incomplete_data = {
            "origin_address": "123 Main St"
            # Missing destination_address
        }
        
        response = client.post('/api/quotes',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

class TestAppointmentModification:
    """Test appointment modification functionality."""
    
    @patch('enhanced_app.requests.put')
    @patch('enhanced_app.requests.get')
    def test_modify_appointment_success(self, mock_get, mock_put, client):
        """Test successful appointment modification."""
        # Mock getting existing appointment
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'id': 1, 'status': 'scheduled'}
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response
        
        # Mock updating appointment
        mock_put_response = Mock()
        mock_put_response.status_code = 200
        mock_put_response.json.return_value = {'id': 1, 'status': 'scheduled', 'appointment_date': '2024-03-25'}
        mock_put_response.raise_for_status.return_value = None
        mock_put.return_value = mock_put_response
        
        modification_data = {
            "new_date": "2024-03-25",
            "new_time": "15:00"
        }
        
        response = client.put('/api/appointments/1',
                            data=json.dumps(modification_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'appointment_id' in data
        assert 'status' in data
        assert data['status'] == 'modified'

class TestHealthCheck:
    """Test health check endpoint."""
    
    @patch('enhanced_app.requests.get')
    def test_health_check_success(self, mock_get, client):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
        assert 'dependencies' in data
        assert data['status'] == 'healthy'

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_404_handler(self, client):
        """Test 404 error handling."""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON data."""
        response = client.post('/api/appointments',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

