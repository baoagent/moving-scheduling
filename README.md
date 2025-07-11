# Moving Company MVP - Technical Architecture (Free/Open Source)

## System Overview

**Core Value Proposition**: AI-powered scheduling agent that handles inbound leads, books moves, and reduces no-shows through intelligent follow-up sequences.

## Architecture Components (FREE OPTIONS)

### 1. Communication Layer
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Phone Calls   │    │   SMS/Text      │    │   Web Form      │
│   (FREE LIMIT)  │    │   (FREE LIMIT)  │    │   (React)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  AI Orchestrator │
                    │  (Ollama+Llama3)│
                    └─────────────────┘
```

### FREE Tech Stack Options

#### Communication Services
**Phone/SMS (Free Options)**:
- **Twilio**: $15 free credits (then $1/month + usage)
- **Alternative**: TextBelt API (free tier: 1 text/day, then $0.01/text)
- **Alternative**: Use Google Voice number + automation scripts
- **Tradeoff**: Limited volume, need to upgrade quickly for real usage

**Voice Recognition (Free)**:
- **OpenAI Whisper** (self-hosted, completely free)
- **Alternative**: Google Speech-to-Text (free tier: 60 minutes/month)
- **Tradeoff**: Self-hosted requires more setup, cloud has usage limits

#### AI Services
**LLM Options (Free)**:
- **Ollama + Llama 3.1** (completely free, self-hosted)
- **Google Gemini**: Free tier (15 requests/minute)
- **OpenAI**: $5 free credits (then $0.002/1K tokens)
- **Tradeoff**: Self-hosted requires good hardware, cloud options have usage limits

#### Database & Backend
**Database (Free)**:
- **PostgreSQL** (completely free, self-hosted)
- **Supabase**: Free tier (50MB database, 50MB storage)
- **PlanetScale**: Free tier (5GB storage, 1 billion reads/month)
- **Tradeoff**: Self-hosted requires management, cloud has storage limits

**Backend Framework (Free)**:
- **Node.js + Express** (completely free)
- **Python + FastAPI** (completely free)
- **Next.js** (completely free)

#### Hosting (Free)**:
- **Railway**: Free tier ($5/month credit)
- **Render**: Free tier (750 hours/month)
- **Vercel**: Free tier (hobby projects)
- **Fly.io**: Free tier (3 shared VMs)
- **Tradeoff**: Free tiers have resource limits and may sleep

### 2. Core Services

#### A. Lead Capture & Qualification Service
**Input**: Phone call, SMS, or web form
**Process**:
- Extract key information (date, origin, destination, size)
- Qualify lead (budget, timeline, special requirements)
- Determine crew/truck requirements
- Check availability

**AI Prompt Framework (for Llama 3.1)**:
```
You are a moving company booking assistant. Extract these details:
- Moving date (required)
- Origin address (required)
- Destination address (required)
- Home size (studio, 1BR, 2BR, 3BR, 4BR+)
- Special items (piano, artwork, fragile items)
- Budget range
- Preferred time window
- Contact information

If any required info is missing, ask clarifying questions.
Respond in JSON format with extracted data and next_action.
```

#### B. Availability Management Service
**Data Structure**:
```json
{
  "crews": [
    {
      "id": "crew_001",
      "size": 3,
      "skills": ["piano", "stairs", "long_distance"],
      "availability": {
        "2025-07-15": {
          "morning": "available",
          "afternoon": "available",
          "evening": "maintenance"
        }
      }
    }
  ]
}
```

#### C. Booking Confirmation Service
**Free Email Options**:
- **Nodemailer + Gmail SMTP** (free for personal use)
- **EmailJS** (free tier: 200 emails/month)
- **Resend**: Free tier (100 emails/month)

**SMS Options**:
- **TextBelt**: Free tier (1 text/day, then $0.01/text)
- **46elks**: Free trial credits
- **Tradeoff**: Very limited free SMS, need paid service for real usage

### 3. Database Schema (PostgreSQL)

```sql
-- Jobs table
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_email VARCHAR(255),
    origin_address TEXT NOT NULL,
    destination_address TEXT NOT NULL,
    move_date DATE NOT NULL,
    move_time_slot VARCHAR(20), -- 'morning', 'afternoon', 'evening'
    home_size VARCHAR(20) NOT NULL,
    special_items TEXT[],
    estimated_hours INTEGER,
    estimated_cost DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'confirmed', 'completed', 'cancelled'
    assigned_crew_id INTEGER,
    assigned_truck_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crews table
CREATE TABLE crews (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    size INTEGER NOT NULL,
    skills TEXT[],
    hourly_rate DECIMAL(10,2)
);

-- Trucks table
CREATE TABLE trucks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    size VARCHAR(20) NOT NULL,
    equipment TEXT[],
    daily_rate DECIMAL(10,2)
);

-- Availability table
CREATE TABLE availability (
    id SERIAL PRIMARY KEY,
    resource_type VARCHAR(20) NOT NULL, -- 'crew' or 'truck'
    resource_id INTEGER NOT NULL,
    date DATE NOT NULL,
    time_slot VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'available' -- 'available', 'booked', 'maintenance'
);
```

### 4. MVP Implementation Plan

#### Phase 1: Basic Web Demo (Week 1-2)
**Tech Stack**:
- Frontend: React (Vite) + Tailwind CSS
- Backend: Node.js + Express
- Database: PostgreSQL (local)
- AI: Ollama + Llama 3.1 (local)

**Features**:
- Web form for quote requests
- Simple availability checker
- Basic crew/truck assignment logic
- Email confirmations

#### Phase 2: SMS Integration (Week 3)
**Add**:
- TextBelt integration for SMS
- Simple SMS bot for booking confirmation
- Customer can text to confirm/reschedule

#### Phase 3: Voice Integration (Week 4)
**Add**:
- Basic phone number (Google Voice)
- Whisper for speech-to-text
- Text-to-speech for responses

### 5. Demo Strategy

#### A. Sample Data Setup
```json
{
  "sample_company": {
    "name": "NYC Quick Movers",
    "crews": [
      {"id": 1, "name": "Team Alpha", "size": 3, "skills": ["piano", "stairs"]},
      {"id": 2, "name": "Team Beta", "size": 2, "skills": ["apartments", "quick"]}
    ],
    "trucks": [
      {"id": 1, "name": "Big Blue", "size": "26ft"},
      {"id": 2, "name": "Small Red", "size": "16ft"}
    ]
  }
}
```

#### B. Demo Script
1. **Show incoming lead** (web form or SMS)
2. **AI extracts info** and suggests crew/truck
3. **Check availability** in real-time
4. **Send confirmation** via email/SMS
5. **Show follow-up sequence** (24hr, 48hr reminders)

### 6. Cost Breakdown

#### Completely Free Option (Local Development)
- **Compute**: Your laptop (Ollama + Llama 3.1)
- **Database**: PostgreSQL (local)
- **Email**: Gmail SMTP (free)
- **SMS**: TextBelt (1 free/day)
- **Total**: $0/month

#### Minimal Paid Option (Production Ready)
- **Hosting**: Railway ($5/month credit covers small usage)
- **Database**: Supabase free tier
- **AI**: OpenAI ($5 free credits, then ~$10/month)
- **SMS**: TextBelt ($0.01/text after free tier)
- **Total**: ~$15/month for light usage

#### Upgrade Path
- **Phone**: Twilio ($15 setup + $1/month + usage)
- **SMS**: Twilio ($0.0075/SMS)
- **Hosting**: Railway/Render ($20-50/month)
- **AI**: OpenAI ($50-100/month with volume)
- **Total**: $100-200/month for real business usage

### 7. Next Steps

1. **Build local demo** with sample data
2. **Test with mock scenarios** (different home sizes, special requirements)
3. **Create demo video** showing the full workflow
4. **Prepare cost-savings presentation** for moving companies
5. **Identify 3-5 target companies** for outreach

Would you like me to help you build the actual demo application next?15": {
          "morning": "available",
          "afternoon": "booked",
          "evening": "available"
        }
      }
    }
  ],
  "trucks": [
    {
      "id": "truck_001",
      "size": "26ft",
      "equipment": ["dolly", "straps", "blankets"],
      "availability": {
        "2025-07-