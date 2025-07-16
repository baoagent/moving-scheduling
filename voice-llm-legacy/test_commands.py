#!/usr/bin/env python3
"""
Test script for BaoAgent Service commands
"""

import json
import subprocess
import sys

def test_tts_command():
    """Test TTS command"""
    command = {
        "type": "tts",
        "text": "Hello, my name is BAO Agent. I will help with all your scheduling needs."
    }
    return json.dumps(command)

def test_status_command():
    """Test status command"""
    command = {
        "type": "status"
    }
    return json.dumps(command)

def test_transcribe_command():
    """Test transcribe command with dummy audio data"""
    # Create a simple 1-second silence audio (base64 encoded)
    import base64
    
    # Generate 1 second of silence at 16kHz (16000 samples of 0)
    silence_bytes = b'\x00\x00' * 16000  # 16-bit samples of 0
    audio_b64 = base64.b64encode(silence_bytes).decode('utf-8')
    
    command = {
        "type": "transcribe",
        "audio_data": audio_b64,
        "sample_rate": 16000
    }
    return json.dumps(command)

def main():
    print("BaoAgent Service Test Commands")
    print("=" * 40)
    
    print("\n1. TTS Command:")
    print(test_tts_command())
    
    print("\n2. Status Command:")
    print(test_status_command())
    
    print("\n3. Transcribe Command (with silence):")
    print(test_transcribe_command())
    
    print("\nTo test with the service:")
    print("1. Start the service: python3 baoagent_service.py")
    print("2. Copy and paste one of the JSON commands above")
    print("3. Press Enter to send the command")

if __name__ == "__main__":
    main() 