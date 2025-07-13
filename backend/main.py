"""
BaoAgent Moving Scheduling Backend
FastAPI backend for moving scheduling workflow
"""

import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Add the shared client to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared', 'llm-client'))

from client import create_baoagent_client

app = FastAPI(title="BaoAgent Moving Scheduling", version="1.0.0")

# Initialize LLM client
llm_client = create_baoagent_client()

class MovingRequest(BaseModel):
    message: str
    phone_number: Optional[str] = None
    user_context: Optional[dict] = None

class MovingResponse(BaseModel):
    response: str
    suggested_actions: Optional[list] = None

@app.get("/")
async def root():
    return {"message": "BaoAgent Moving Scheduling API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    llm_healthy = llm_client.health_check()
    return {
        "status": "healthy" if llm_healthy else "unhealthy",
        "llm_service": "available" if llm_healthy else "unavailable"
    }

@app.post("/chat", response_model=MovingResponse)
async def chat_endpoint(request: MovingRequest):
    """Main chat endpoint for moving scheduling"""
    
    try:
        # Create system prompt for moving scheduling
        system_prompt = """You are a helpful assistant for BaoAgent's moving scheduling service. 
        Help users schedule their moving appointments, provide moving tips, and answer questions about moving services.
        Be friendly, professional, and focused on moving-related topics."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message}
        ]
        
        # Get response from LLM
        response = llm_client.chat(messages, max_tokens=500, temperature=0.7)
        
        # TODO: Add logic to extract suggested actions from response
        suggested_actions = []
        
        return MovingResponse(
            response=response,
            suggested_actions=suggested_actions
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/sms")
async def sms_webhook(request: MovingRequest):
    """Webhook endpoint for SMS (Twilio)"""
    # TODO: Implement SMS webhook logic
    chat_response = await chat_endpoint(request)
    return {"message": chat_response.response}

@app.post("/schedule")
async def schedule_moving(request: MovingRequest):
    """Specific endpoint for scheduling moving appointments"""
    
    try:
        # Enhanced prompt for scheduling
        scheduling_prompt = f"""You are helping a user schedule a moving appointment. 
        User message: {request.message}
        
        Please help them with:
        1. Determining their moving needs (size, distance, date)
        2. Suggesting available time slots
        3. Collecting necessary information
        4. Providing moving tips if relevant
        
        Be specific and helpful."""
        
        messages = [{"role": "user", "content": scheduling_prompt}]
        response = llm_client.chat(messages, max_tokens=500, temperature=0.7)
        
        return MovingResponse(response=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scheduling moving: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
