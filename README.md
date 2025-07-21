# Enhanced Moving Scheduling MCP Server

A comprehensive Model Context Protocol (MCP) server designed for voice-controlled moving appointment scheduling. This server provides a robust API that integrates seamlessly with LLM function calling and voice agents.

## 🎯 Overview

This MCP server acts as an intelligent middleware layer between voice agents (like baoagent-voice-server) and the core moving-scheduling-server. It provides:

- **LLM-Optimized API**: Structured endpoints designed for function calling
- **Voice Agent Integration**: Seamless integration with OpenAI Realtime API
- **Comprehensive Validation**: Input validation and error handling
- **Service Quotes**: Automated pricing calculations
- **Appointment Management**: Full CRUD operations for appointments

## 🏗️ Architecture

```
Voice Call → Twilio → Voice Server → OpenAI Realtime API
                                           ↓
                                    Function Calling
                                           ↓
                                    MCP Server (This)
                                           ↓
                                Moving Scheduling Server
                                           ↓
                                      Database
```

## 🚀 Features

### Core Functionality
- **Availability Checking**: Real-time appointment slot availability
- **Appointment Scheduling**: Create, modify, and cancel appointments
- **Customer Management**: Automatic customer creation and lookup
- **Service Quotes**: Dynamic pricing based on service type and requirements
- **Phone-based Lookup**: Find appointments using customer phone numbers

### LLM Integration
- **Tool Definitions**: Pre-configured function definitions for OpenAI
- **Structured Responses**: Consistent JSON responses for reliable parsing
- **Error Handling**: Graceful error responses with helpful messages
- **Validation**: Comprehensive input validation with detailed error reporting

### Enhanced Features
- **CORS Support**: Cross-origin requests for frontend integration
- **Health Monitoring**: Health check endpoints for system monitoring
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Type Safety**: Full TypeScript-style schemas with Python dataclasses

## 📋 API Endpoints

### Tool Definitions
- `GET /api/tools` - Returns LLM function calling definitions

### Appointment Management
- `GET /api/availability?date=YYYY-MM-DD` - Check available time slots
- `POST /api/appointments` - Create new appointment
- `GET /api/appointments/by-phone/{phone}` - Get customer appointments
- `PUT /api/appointments/{id}` - Modify existing appointment
- `DELETE /api/appointments/{id}` - Cancel appointment

### Service Quotes
- `POST /api/quotes` - Get service pricing estimates

### System
- `GET /api/health` - Health check and system status

## 🛠️ LLM Function Tools

The server exposes 6 main tools for LLM function calling:

1. **check_appointment_availability** - Check available time slots
2. **create_appointment** - Schedule new appointments
3. **get_customer_appointments** - Lookup customer appointments
4. **cancel_appointment** - Cancel existing appointments
5. **get_service_quote** - Generate pricing estimates
6. **modify_appointment** - Update appointment details

## 📊 Data Schemas

### Appointment Creation
```json
{
  "customer_phone": "555-1234",
  "customer_name": "John Doe",
  "appointment_date": "2024-03-15",
  "appointment_time": "14:00",
  "origin_address": "123 Main St",
  "destination_address": "456 Oak Ave",
  "notes": "Handle with care",
  "service_type": "residential_move",
  "estimated_hours": 3
}
```

### Service Quote Request
```json
{
  "origin_address": "123 Main St",
  "destination_address": "456 Oak Ave",
  "service_type": "residential_move",
  "estimated_hours": 4,
  "special_items": ["piano", "artwork"]
}
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.11+
- Flask 2.3.3+
- Access to moving-scheduling-server API

### Installation
```bash
# Clone the repository
git clone https://github.com/baoagent/moving-scheduling-mcp.git
cd moving-scheduling-mcp

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SCHEDULING_API_URL="http://your-scheduling-server:5001/api"

# Run the server
python enhanced_app.py
```

### Docker Deployment
```bash
# Build the image
docker build -t moving-scheduling-mcp .

# Run the container
docker run -p 5002:5002 \
  -e SCHEDULING_API_URL="http://scheduling-server:5001/api" \
  moving-scheduling-mcp
```

## 🧪 Testing

The server includes a comprehensive test suite covering all endpoints and edge cases:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_enhanced_mcp.py::TestToolDefinitions -v
python -m pytest tests/test_enhanced_mcp.py::TestAppointmentCreation -v
```

### Test Coverage
- ✅ Tool definition validation
- ✅ Availability checking with edge cases
- ✅ Appointment creation and validation
- ✅ Customer lookup and management
- ✅ Appointment cancellation
- ✅ Service quote generation
- ✅ Error handling and edge cases
- ✅ Health check functionality

## 🔗 Integration with Voice Server

### Function Calling Setup
The voice server should register these tools with OpenAI:

```python
# In baoagent-voice-server
import requests

# Get tool definitions from MCP server
response = requests.get("http://mcp-server:5002/api/tools")
tools = response.json()["tools"]

# Register with OpenAI session
session_config = {
    "tools": tools,
    "instructions": "Use the available tools to help customers schedule moving appointments..."
}
```

### Tool Invocation
When OpenAI calls a function, the voice server should forward to MCP:

```python
def invoke_mcp_tool(tool_name: str, tool_arguments: dict):
    # Map tool names to MCP endpoints
    endpoint_map = {
        "check_appointment_availability": "/api/availability",
        "create_appointment": "/api/appointments",
        "get_customer_appointments": "/api/appointments/by-phone/{phone}",
        # ... etc
    }
    
    # Forward to MCP server
    response = requests.post(f"http://mcp-server:5002{endpoint}", json=tool_arguments)
    return response.json()
```

## 📈 Performance & Monitoring

### Health Monitoring
The server provides health check endpoints that monitor:
- Server status and uptime
- Dependency health (scheduling API connectivity)
- Version information
- System metrics

### Logging
Comprehensive logging includes:
- Request/response logging
- Error tracking with context
- Performance metrics
- Security events

### Scalability
- Stateless design for horizontal scaling
- Connection pooling for external APIs
- Efficient request validation
- Caching-ready architecture

## 🔒 Security Features

### Input Validation
- Comprehensive data validation using schemas
- SQL injection prevention
- XSS protection
- Rate limiting ready

### Error Handling
- Sanitized error messages
- No sensitive data exposure
- Graceful degradation
- Comprehensive logging

## 🚀 Deployment Considerations

### Environment Variables
- `SCHEDULING_API_URL`: URL of the core scheduling server
- `FLASK_ENV`: Environment (production/development)
- `LOG_LEVEL`: Logging verbosity

### Production Setup
- Use WSGI server (Gunicorn recommended)
- Configure reverse proxy (Nginx)
- Set up SSL/TLS termination
- Configure monitoring and alerting

### High Availability
- Deploy multiple instances behind load balancer
- Health check configuration for load balancer
- Database connection pooling
- Circuit breaker pattern for external APIs

## 📝 Version History

### v1.1.0 (Current)
- Enhanced API with comprehensive tool definitions
- Added service quote functionality
- Improved error handling and validation
- Comprehensive test suite
- Full documentation

### v1.0.0 (Legacy)
- Basic appointment scheduling
- Simple availability checking
- Customer management
- Basic error handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the comprehensive test suite for usage examples
- Review the API documentation above
- Check logs for detailed error information
- Contact the development team for integration support

