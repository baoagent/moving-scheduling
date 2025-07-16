Moving Company MVP - Voice AI Architecture
System Overview
Core Value Proposition: AI voice agent that handles inbound calls, books moves, and reduces no-shows through intelligent follow-up sequences.
Key Architecture Change: Using a voice AI platform eliminates the need for separate voice recognition, text-to-speech, and LLM orchestration. The only custom component needed is an MCP server for your booking system.
Voice AI Platform Options
Option 1: Twilio Voice + OpenAI Realtime API (Cheapest)
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Phone Calls   │    │   SMS/Text      │    │   Web Form      │
│   (Twilio)      │    │   (Twilio)      │    │   (React)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Your Voice    │
                    │   Server        │
                    │ (Node.js/Python)│
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MCP Server    │
                    │ (Your Custom)   │
                    └─────────────────┘
Cost: ~$5-8/month base + $0.0085/minute

Twilio Voice: $1/month + $0.0085/minute
OpenAI Realtime API: $0.006/minute input, $0.024/minute output
Most control, requires more development

Implementation Components
1. Twilio Voice Server (Your Custom)

Language: Node.js/Python
Purpose: Handle Twilio webhooks, manage call flow
Integration: OpenAI Realtime API for speech processing
MCP: Connect to your booking system

2. MCP Server (Same as Before)

Purpose: Interface between voice agent and database
Tools: Availability, booking, confirmations

3. Database

PostgreSQL (same schema)
Hosting: Supabase free tier or self-hosted

Twilio Voice Server Structure
voice-server/
├── package.json
├── src/
│   ├── index.js          # Express server
│   ├── routes/
│   │   ├── voice.js      # Twilio webhook handlers
│   │   └── status.js     # Call status updates
│   ├── services/
│   │   ├── openai.js     # OpenAI Realtime API
│   │   └── mcp.js        # MCP client
│   └── utils/
│       └── twiml.js      # TwiML responses
├── mcp-server/           # Your booking MCP server
│   ├── package.json
│   └── src/
│       ├── index.ts
│       └── tools.ts
└── README.md
Sample Voice Server Code
javascript// src/routes/voice.js
const express = require('express');
const VoiceResponse = require('twilio').twiml.VoiceResponse;
const { createMCPClient } = require('../services/mcp');

const router = express.Router();

router.post('/incoming', async (req, res) => {
  const twiml = new VoiceResponse();
  
  // Connect to OpenAI Realtime API
  twiml.connect().stream({
    url: `wss://${req.get('host')}/media-stream`,
    name: 'booking-assistant'
  });
  
  res.type('text/xml');
  res.send(twiml.toString());
});

// WebSocket handler for OpenAI Realtime API
router.ws('/media-stream', (ws, req) => {
  // Handle media stream with OpenAI
  // Connect to MCP server for booking functions
});
MCP Server Implementation
Required MCP Tools
typescript// mcp-server/src/tools.ts
export const tools = [
  {
    name: "check_availability",
    description: "Check crew and truck availability for a specific date and time",
    inputSchema: {
      type: "object",
      properties: {
        date: { type: "string", format: "date" },
        timeSlot: { type: "string", enum: ["morning", "afternoon", "evening"] },
        location: { type: "string" }
      },
      required: ["date", "timeSlot"]
    }
  },
  {
    name: "create_booking",
    description: "Create a new moving job booking",
    inputSchema: {
      type: "object",
      properties: {
        customer_name: { type: "string" },
        customer_phone: { type: "string" },
        customer_email: { type: "string" },
        origin_address: { type: "string" },
        destination_address: { type: "string" },
        move_date: { type: "string", format: "date" },
        move_time_slot: { type: "string", enum: ["morning", "afternoon", "evening"] },
        home_size: { type: "string" },
        special_items: { type: "array", items: { type: "string" } },
        estimated_hours: { type: "number" },
        estimated_cost: { type: "number" }
      },
      required: ["customer_name", "customer_phone", "origin_address", "destination_address", "move_date", "move_time_slot", "home_size"]
    }
  },
  {
    name: "send_confirmation",
    description: "Send booking confirmation via SMS/email",
    inputSchema: {
      type: "object",
      properties: {
        job_id: { type: "number" },
        method: { type: "string", enum: ["sms", "email", "both"] }
      },
      required: ["job_id", "method"]
    }
  },
  {
    name: "update_job_status",
    description: "Update the status of a moving job",
    inputSchema: {
      type: "object",
      properties: {
        job_id: { type: "number" },
        status: { type: "string", enum: ["pending", "confirmed", "in_progress", "completed", "cancelled"] }
      },
      required: ["job_id", "status"]
    }
  },
  {
    name: "get_job_details",
    description: "Retrieve details of a specific job",
    inputSchema: {
      type: "object",
      properties: {
        job_id: { type: "number" }
      },
      required: ["job_id"]
    }
  }
];
Sample MCP Server Structure
mcp-server/
├── package.json
├── src/
│   ├── index.ts          # MCP server entry point
│   ├── tools.ts          # Tool definitions
│   ├── handlers/
│   │   ├── availability.ts
│   │   ├── booking.ts
│   │   └── notifications.ts
│   ├── database/
│   │   ├── connection.ts
│   │   └── queries.ts
│   └── types/
│       └── index.ts
└── README.md
Database Schema (Same as Before)
sql-- Jobs table
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(20),
    customer_email VARCHAR(255),
    origin_address TEXT NOT NULL,
    destination_address TEXT NOT NULL,
    move_date DATE NOT NULL,
    move_time_slot VARCHAR(20) NOT NULL,
    home_size VARCHAR(20) NOT NULL,
    special_items TEXT[],
    estimated_hours INTEGER,
    estimated_cost DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending',
    assigned_crew_id INTEGER,
    assigned_truck_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crew table
CREATE TABLE crew (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    skills TEXT[]
);

-- Trucks table
CREATE TABLE trucks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    size VARCHAR(20) NOT NULL,
    location VARCHAR(255),
    equipment TEXT[]
);

-- Availability table
CREATE TABLE availability (
    id SERIAL PRIMARY KEY,
    resource_type VARCHAR(20) NOT NULL,
    resource_id INTEGER NOT NULL,
    date DATE NOT NULL,
    time_slot VARCHAR(20) NOT NULL,
    location VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'available'
);
ElevenLabs Agent Configuration
Agent Prompt Template
You are a professional moving company booking assistant for NYC Quick Movers. 

Your responsibilities:
1. Answer incoming calls professionally
2. Collect booking information from customers
3. Check availability using the MCP tools
4. Book confirmed moves
5. Send confirmation messages
6. Handle rescheduling requests

Required Information to Collect:
- Customer name and phone number
- Origin address (where moving from)
- Destination address (where moving to)
- Preferred moving date
- Time preference (morning, afternoon, evening)
- Home size (studio, 1BR, 2BR, 3BR, 4BR+)
- Special items (piano, artwork, etc.)
- Any special requirements

Pricing Structure:
- Studio/1BR: $400-600 (2-4 hours)
- 2BR: $600-900 (4-6 hours)
- 3BR: $900-1200 (6-8 hours)
- 4BR+: $1200+ (8+ hours)

Always use the MCP tools to:
- Check availability before confirming
- Create bookings in the system
- Send confirmations to customers

Be friendly, professional, and efficient. If you can't help with something, explain why and offer alternatives.
MCP Server Connection
In your ElevenLabs agent settings:

Add MCP server URL: https://your-server.com/mcp
Configure authentication (API key)
Set approval settings for each tool
Test the connection

Cost Comparison (100 calls/month, 5 min avg)
Twilio + OpenAI Realtime (Recommended)

Twilio Voice: $1 + (100 × 5 × $0.0085) = $5.25
OpenAI Realtime: 100 × 5 × ($0.006 + $0.024) = $15
MCP Server Hosting: $5
SMS confirmations: $0.75
Total: ~$26/month

Twilio + Speech Recognition + GPT-4

Twilio Voice: $5.25 (same as above)
Speech Recognition: 100 × 5 × $0.02 = $10
GPT-4 API: ~$5 (estimated)
Azure TTS: ~$2
Hosting: $5
SMS: $0.75
Total: ~$28/month

ElevenLabs (For Comparison)

ElevenLabs: $10 + (100 × 5 × $0.18) = $100
Hosting: $5
SMS: $0.75
Total: ~$106/month

DIY Solution (Most Work)

Twilio Voice: $5.25
Self-hosted everything else: $5 (hosting only)
SMS: $0.75
Total: ~$11/month

Implementation Steps
Phase 1: MCP Server (Week 1)

Set up PostgreSQL database
Build MCP server with booking tools
Test locally with MCP client
Deploy to Railway/Render

Phase 2: Twilio Voice Integration (Week 2)

Set up Twilio Voice webhooks
Build voice server with OpenAI Realtime API
Connect MCP server to voice server
Test basic call flow

Phase 3: SMS & Full Integration (Week 3)

Add SMS confirmations via Twilio
Implement full booking workflow
Add error handling and fallbacks
Test with real phone calls

Phase 4: Web Interface (Week 4)

Build React frontend
Connect to same MCP server
Add admin dashboard
Polish and deploy

Demo Strategy
Sample Conversation Flow
Customer: "Hi, I need to book a move for next Friday."
Agent: "I'd be happy to help you book a move! Let me get some details. What's your name and phone number?"
Customer: "John Smith, 555-0123"
Agent: "Great! What's your current address where we'll be moving from?"
Customer: "123 Main Street, Brooklyn, NY"
Agent: "And where are you moving to?"
Customer: "456 Oak Avenue, Queens, NY"
Agent: "Perfect! What size home are you moving? Studio, 1 bedroom, 2 bedroom, etc?"
Customer: "It's a 2-bedroom apartment"
Agent: "Excellent! Let me check our availability for Friday. What time would work best - morning, afternoon, or evening?"
Customer: "Morning would be great"
Agent: Uses check_availability tool "Good news! We have availability Friday morning. Based on a 2-bedroom move, this would typically take 4-6 hours and cost between $600-900. Would you like to book this slot?"
Customer: "Yes, please!"
Agent: Uses create_booking tool "Perfect! I've booked your move for Friday morning. You'll receive a confirmation text shortly with all the details. Is there anything else I can help you with?"