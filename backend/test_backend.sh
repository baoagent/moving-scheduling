#!/bin/bash
# Test script for Moving Scheduling Backend

source venv/bin/activate

echo "🧪 Testing Moving Scheduling Backend..."

# Start the backend server in background
python main.py &
BACKEND_PID=$!

# Wait for server to start
sleep 3

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost:8001/health | python -m json.tool

# Test chat endpoint
echo -e "\nTesting chat endpoint..."
curl -X POST "http://localhost:8001/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "I need help scheduling a move for next week"}' | python -m json.tool

# Test schedule endpoint
echo -e "\nTesting schedule endpoint..."
curl -X POST "http://localhost:8001/schedule" \
    -H "Content-Type: application/json" \
    -d '{"message": "I need to move a 2-bedroom apartment from NYC to Boston"}' | python -m json.tool

# Clean up
kill $BACKEND_PID
echo -e "\n✅ Backend tests completed!"
