#!/usr/bin/env python3
"""
BaoAgent Client - Client for the persistent STT and TTS service
"""

import subprocess
import json
import base64
import numpy as np
import soundfile as sf
import tempfile
import os
import time

class BaoAgentClient:
    def __init__(self, service_script="baoagent_service.py"):
        self.service_script = service_script
        self.process = None
        self.service_ready = False
        
    def start_service(self):
        """Start the BaoAgent service as a subprocess."""
        if self.process is None:
            print("Starting BaoAgent service...")
            self.process = subprocess.Popen(
                ["python3", self.service_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Wait for service to be ready
            while True:
                line = self.process.stdout.readline().strip()
                if "Service ready!" in line:
                    self.service_ready = True
                    print("Service is ready!")
                    break
                elif not line:
                    time.sleep(0.1)
                else:
                    print(f"Service: {line}")
    
    def stop_service(self):
        """Stop the BaoAgent service."""
        if self.process:
            self.process.stdin.write("quit\n")
            self.process.stdin.flush()
            self.process.wait()
            self.process = None
            self.service_ready = False
    
    def send_command(self, command):
        """Send a JSON command to the service and return the response."""
        if not self.service_ready:
            self.start_service()
        
        try:
            # Send command
            self.process.stdin.write(json.dumps(command) + "\n")
            self.process.stdin.flush()
            
            # Read response - keep reading until we get valid JSON
            while True:
                line = self.process.stdout.readline().strip()
                if not line:
                    time.sleep(0.1)
                    continue
                
                # Try to parse as JSON
                try:
                    response = json.loads(line)
                    return response
                except json.JSONDecodeError:
                    # This line is not JSON, continue reading
                    print(f"Service debug: {line}")
                    continue
                    
        except Exception as e:
            print(f"Error communicating with service: {e}")
            return None
    
    def transcribe_audio(self, audio_data, sample_rate=16000):
        """Transcribe audio using the service."""
        # Convert audio to base64
        if isinstance(audio_data, np.ndarray):
            audio_bytes = audio_data.tobytes()
        else:
            audio_bytes = audio_data
        
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        command = {
            'type': 'transcribe',
            'audio_data': audio_b64,
            'sample_rate': sample_rate
        }
        
        response = self.send_command(command)
        if response and response.get('success'):
            return response.get('text', '')
        else:
            print(f"Transcription failed: {response}")
            return None
    
    def text_to_speech(self, text):
        """Generate speech from text using the service."""
        command = {
            'type': 'tts',
            'text': text
        }
        
        response = self.send_command(command)
        if response and response.get('success'):
            # Convert base64 audio back to numpy array
            audio_b64 = response.get('audio_data', '')
            audio_bytes = base64.b64decode(audio_b64)
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            return audio_data
        else:
            print(f"TTS failed: {response}")
            return None
    
    def get_status(self):
        """Get the status of the service."""
        command = {'type': 'status'}
        return self.send_command(command)
    
    def save_audio(self, audio_data, filename, sample_rate=24000):
        """Save audio data to a file."""
        sf.write(filename, audio_data, sample_rate)
        print(f"Audio saved to {filename}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_service()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_service()

# Example usage and testing
def test_service():
    """Test the BaoAgent service with a simple workflow."""
    client = BaoAgentClient()
    
    try:
        # Start the service
        client.start_service()
        
        # Test TTS
        print("Testing TTS...")
        text = "Hello, this is a test of the BaoAgent service."
        audio_data = client.text_to_speech(text)
        
        if audio_data is not None:
            # Save the generated audio
            client.save_audio(audio_data, "test_output.wav")
            
            # Test STT with the generated audio
            print("Testing STT...")
            transcription = client.transcribe_audio(audio_data)
            
            if transcription:
                print(f"Original text: {text}")
                print(f"Transcription: {transcription}")
            else:
                print("STT failed")
        else:
            print("TTS failed")
        
        # Get service status
        status = client.get_status()
        print(f"Service status: {status}")
        
    finally:
        client.stop_service()

if __name__ == "__main__":
    test_service() 