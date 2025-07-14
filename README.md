Free Voice-to-LLM Phone System Implementation Guide (Mac Mini Updated)
Architecture Overview
Incoming Call → WebRTC → Audio Stream → STT → LLM → TTS → Audio Response
Component 1: Phone Interface Layer (FREE) - Mac Compatible
Solution: Simple WebRTC + WebSocket (No Asterisk needed)
Why skip Asterisk?

Asterisk is no longer available on Homebrew for Mac
Complex installation process on modern macOS
Overkill for a simple voice-to-LLM system

Alternative: Direct WebRTC Implementation
javascript// Pure WebRTC solution - works in any browser
// No server-side phone system needed
Component 2: Speech Processing Layer (FREE) - Mac Optimized
STT Solution: OpenAI Whisper (Local/Free)
Installation (Mac Mini 16GB):
bash# Use conda for better Mac compatibility
brew install miniconda
conda create -n voice-llm python=3.10
conda activate voice-llm

# Install Whisper with Mac optimizations
pip install openai-whisper
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# For Apple Silicon Macs (M1/M2/M3)
export PYTORCH_ENABLE_MPS_FALLBACK=1
Mac-Optimized STT Implementation:
python

import whisper
import numpy as np
import torch
import queue
import threading
import librosa

class MacOptimizedSTT:
    def __init__(self, model_size="base"):
        # Use MPS on Apple Silicon, CPU otherwise
        if torch.backends.mps.is_available():
            device = "mps"
            print("Using Apple Silicon MPS acceleration")
        else:
            device = "cpu"
            print("Using CPU")
            
        self.model = whisper.load_model(model_size, device=device)
        self.audio_buffer = []
        self.text_callback = None
        self.min_audio_length = 1.0  # seconds
        
    def process_audio_chunk(self, audio_data, sample_rate=16000):
        """Process incoming audio with simple energy-based VAD"""
        # Convert to float32 for processing
        if isinstance(audio_data, np.ndarray):
            audio_float = audio_data.astype(np.float32) / 32768.0
        else:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0
        
        # Simple energy-based voice activity detection
        energy = np.mean(audio_float ** 2)
        
        if energy > 0.01:  # Adjust threshold as needed
            self.audio_buffer.append(audio_float)
        else:
            # Silence detected, process accumulated audio
            if len(self.audio_buffer) > 0:
                self.transcribe_accumulated()
    
    def transcribe_accumulated(self):
        """Transcribe accumulated audio chunks"""
        if len(self.audio_buffer) == 0:
            return
            
        # Combine audio chunks
        combined_audio = np.concatenate(self.audio_buffer)
        
        # Check minimum length
        if len(combined_audio) / 16000 < self.min_audio_length:
            return
            
        try:
            result = self.model.transcribe(
                combined_audio,
                fp16=False,  # Use fp32 for better Mac compatibility
                language="en",
                initial_prompt="This is a phone conversation."
            )
            
            if self.text_callback and result["text"].strip():
                self.text_callback(result["text"].strip())
                
        except Exception as e:
            print(f"Transcription error: {e}")
        finally:
            self.audio_buffer = []  # Clear buffer
TTS Solution: kyutai/tts-1.6b-en_fr (Moshi TTS, Local/Free)
Installation:
```bash
pip install moshi-mlx soundfile
```
- For Apple Silicon Macs (M1/M2/M3), moshi-mlx uses MLX for hardware acceleration.
- For Intel Macs or other platforms, see the [delayed-streams-modeling repo](https://github.com/kyutai-labs/delayed-streams-modeling) for PyTorch or Rust options.

Mac-Optimized TTS Implementation (Moshi TTS):
```python
import moshi_mlx
import numpy as np
import tempfile
import soundfile as sf

class MacOptimizedTTS:
    def __init__(self, voice="en-us-amy"):
        self.voice = voice  # Use a preset voice embedding from kyutai/tts-voices
        self.sample_rate = 24000  # Moshi TTS default

    def text_to_audio_sync(self, text):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            moshi_mlx.run_inference(
                text=text,
                output_path=tmp_file.name,
                voice=self.voice,
                quantize=8  # For faster inference
            )
            audio_data, _ = sf.read(tmp_file.name, dtype='int16')
        return audio_data

    def text_to_audio_chunks(self, text, chunk_size=4096):
        audio_data = self.text_to_audio_sync(text)
        chunks = []
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            chunks.append(chunk)
        return chunks
```
- This replaces the previous edge-tts-based implementation.
- You can select a voice embedding from the [kyutai/tts-voices](https://huggingface.co/kyutai/tts-voices) repository.
Component 3: LLM Integration Layer (FREE)
Your existing baoagent-llm-client integration:
pythonimport sys
import os
sys.path.append('/Users/kevinsu/baoagent/baoagent-llm-client')
from client import create_baoagent_client

class VoiceLLMAdapter:
    def __init__(self):
        self.client = create_baoagent_client()
        self.conversation_history = []
        
    def process_voice_input(self, text):
        """Process voice input and return response"""
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": text})
        
        # Get response from LLM
        response = self.client.chat(
            messages=self.conversation_history,
            max_tokens=150,  # Keep responses short for voice
            temperature=0.7,
            stream=False
        )
        
        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep history manageable (last 6 messages)
        if len(self.conversation_history) > 6:
            self.conversation_history = self.conversation_history[-6:]
            
        return response
Component 4: Audio Pipeline Manager (FREE)
FastAPI + WebSockets implementation:
pythonfrom fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import base64
import numpy as np
import uvicorn
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class AudioPipelineManager:
    def __init__(self):
        self.stt = MacOptimizedSTT()
        self.tts = MacOptimizedTTS()
        self.llm = VoiceLLMAdapter()
        self.active_connections = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def handle_websocket(self, websocket: WebSocket):
        await websocket.accept()
        connection_id = id(websocket)
        self.active_connections[connection_id] = {
            'websocket': websocket,
            'state': 'listening'
        }
        
        # Setup STT callback
        self.stt.text_callback = lambda text: asyncio.create_task(
            self.handle_stt_result(connection_id, text)
        )
        
        try:
            while True:
                data = await websocket.receive_text()
                await self.process_audio_message(connection_id, data)
        except WebSocketDisconnect:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
    
    async def process_audio_message(self, connection_id, message):
        if connection_id not in self.active_connections:
            return
            
        conn = self.active_connections[connection_id]
        websocket = conn['websocket']
        
        try:
            data = json.loads(message)
            
            if data['type'] == 'audio':
                # Decode audio data
                audio_data = base64.b64decode(data['audio'])
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Process with STT in background
                loop = asyncio.get_event_loop()
                loop.run_in_executor(
                    self.executor,
                    self.stt.process_audio_chunk,
                    audio_array
                )
                
        except Exception as e:
            print(f"Error processing audio: {e}")
    
    async def handle_stt_result(self, connection_id, text):
        if connection_id not in self.active_connections:
            return
            
        conn = self.active_connections[connection_id]
        websocket = conn['websocket']
        
        try:
            if text.strip():
                conn['state'] = 'processing'
                
                # Send transcription to client
                await websocket.send_text(json.dumps({
                    'type': 'transcription',
                    'text': text
                }))
                
                # Process with LLM in background
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    self.executor,
                    self.llm.process_voice_input,
                    text
                )
                
                # Convert response to audio and stream
                conn['state'] = 'responding'
                audio_chunks = await loop.run_in_executor(
                    self.executor,
                    self.tts.text_to_audio_chunks,
                    response
                )
                
                # Send audio chunks
                for chunk in audio_chunks:
                    if len(chunk) > 0:
                        audio_b64 = base64.b64encode(chunk.tobytes()).decode()
                        await websocket.send_text(json.dumps({
                            'type': 'audio_response',
                            'audio': audio_b64
                        }))
                
                conn['state'] = 'listening'
                
        except Exception as e:
            print(f"Error handling STT result: {e}")

# Initialize pipeline
pipeline_manager = AudioPipelineManager()

@app.websocket("/voice")
async def voice_websocket(websocket: WebSocket):
    await pipeline_manager.handle_websocket(websocket)

@app.get("/")
async def root():
    return {"message": "Voice-to-LLM System Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
Component 5: Frontend (No Asterisk/SIP needed)
Pure WebRTC Browser Client:
html<!DOCTYPE html>
<html>
<head>
    <title>Voice-to-LLM Phone (Mac Compatible)</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .listening { background-color: #e8f5e8; }
        .processing { background-color: #fff3cd; }
        .responding { background-color: #d4edda; }
        button { padding: 10px 20px; font-size: 16px; margin: 5px; }
        #transcription { padding: 10px; background: #f8f9fa; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Voice-to-LLM Phone System</h1>
        <button id="startButton">Start Call</button>
        <button id="stopButton" disabled>Stop Call</button>
        <div id="status" class="status">Ready</div>
        <div id="transcription"></div>
        <audio id="audioPlayer" autoplay></audio>
    </div>

    <script>
        class VoiceToLLMPhone {
            constructor() {
                this.websocket = null;
                this.mediaRecorder = null;
                this.audioContext = null;
                this.isRecording = false;
                this.audioChunks = [];
                
                this.startButton = document.getElementById('startButton');
                this.stopButton = document.getElementById('stopButton');
                this.status = document.getElementById('status');
                this.transcription = document.getElementById('transcription');
                
                this.setupEventListeners();
            }
            
            setupEventListeners() {
                this.startButton.addEventListener('click', () => this.startCall());
                this.stopButton.addEventListener('click', () => this.stopCall());
            }
            
            updateStatus(message, className = 'listening') {
                this.status.textContent = message;
                this.status.className = `status ${className}`;
            }
            
            async startCall() {
                try {
                    this.updateStatus('Connecting...', 'processing');
                    
                    // Connect to WebSocket
                    this.websocket = new WebSocket('ws://localhost:8000/voice');
                    
                    this.websocket.onopen = () => {
                        this.updateStatus('Connected - Starting audio capture...', 'processing');
                        this.startAudioCapture();
                    };
                    
                    this.websocket.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        this.handleServerMessage(data);
                    };
                    
                    this.websocket.onclose = () => {
                        this.updateStatus('Disconnected', 'processing');
                        this.stopCall();
                    };
                    
                    this.websocket.onerror = (error) => {
                        this.updateStatus('Connection error', 'processing');
                        console.error('WebSocket error:', error);
                    };
                    
                } catch (error) {
                    this.updateStatus('Failed to start call', 'processing');
                    console.error('Error starting call:', error);
                }
            }
            
            async startAudioCapture() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: {
                            sampleRate: 16000,
                            channelCount: 1,
                            echoCancellation: true,
                            noiseSuppression: true
                        }
                    });
                    
                    this.audioContext = new AudioContext({ sampleRate: 16000 });
                    const source = this.audioContext.createMediaStreamSource(stream);
                    
                    // Create script processor for real-time audio
                    const processor = this.audioContext.createScriptProcessor(4096, 1, 1);
                    
                    processor.onaudioprocess = (e) => {
                        if (this.isRecording) {
                            const inputBuffer = e.inputBuffer.getChannelData(0);
                            const audioData = new Int16Array(inputBuffer.length);
                            
                            // Convert float32 to int16
                            for (let i = 0; i < inputBuffer.length; i++) {
                                audioData[i] = Math.max(-1, Math.min(1, inputBuffer[i])) * 0x7FFF;
                            }
                            
                            // Send to server
                            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                                this.websocket.send(JSON.stringify({
                                    type: 'audio',
                                    audio: btoa(String.fromCharCode(...new Uint8Array(audioData.buffer)))
                                }));
                            }
                        }
                    };
                    
                    source.connect(processor);
                    processor.connect(this.audioContext.destination);
                    
                    this.isRecording = true;
                    this.startButton.disabled = true;
                    this.stopButton.disabled = false;
                    this.updateStatus('Listening...', 'listening');
                    
                } catch (error) {
                    this.updateStatus('Microphone access denied', 'processing');
                    console.error('Error accessing microphone:', error);
                }
            }
            
            handleServerMessage(data) {
                switch(data.type) {
                    case 'transcription':
                        this.transcription.innerHTML = `<strong>You said:</strong> ${data.text}`;
                        this.updateStatus('Processing...', 'processing');
                        break;
                    case 'audio_response':
                        this.updateStatus('AI responding...', 'responding');
                        this.playAudio(data.audio);
                        break;
                }
            }
            
            playAudio(audioB64) {
                try {
                    const audioData = atob(audioB64);
                    const audioArray = new Uint8Array(audioData.length);
                    for (let i = 0; i < audioData.length; i++) {
                        audioArray[i] = audioData.charCodeAt(i);
                    }
                    
                    const audioBlob = new Blob([audioArray], { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    const audio = new Audio(audioUrl);
                    audio.play();
                    
                    audio.onended = () => {
                        this.updateStatus('Listening...', 'listening');
                        URL.revokeObjectURL(audioUrl);
                    };
                    
                } catch (error) {
                    console.error('Error playing audio:', error);
                    this.updateStatus('Listening...', 'listening');
                }
            }
            
            stopCall() {
                this.isRecording = false;
                
                if (this.websocket) {
                    this.websocket.close();
                    this.websocket = null;
                }
                
                if (this.audioContext) {
                    this.audioContext.close();
                    this.audioContext = null;
                }
                
                this.startButton.disabled = false;
                this.stopButton.disabled = true;
                this.updateStatus('Ready', 'listening');
            }
        }
        
        // Initialize the phone system
        const phone = new VoiceToLLMPhone();
    </script>
</body>
</html>
Mac Mini Setup Instructions
1. Install Dependencies
bash# Install system dependencies
brew install miniconda python3

# Create virtual environment
conda create -n voice-llm python=3.10
conda activate voice-llm

# Install Python packages (Mac-compatible versions)
pip install fastapi uvicorn websockets
pip install openai-whisper torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install moshi-mlx soundfile
pip install numpy scipy librosa
pip install python-multipart

# For M1/M2/M3 Macs, enable MPS
export PYTORCH_ENABLE_MPS_FALLBACK=1

# Add your baoagent-llm-client to path
export PYTHONPATH="/Users/kevinsu/baoagent/baoagent-llm-client:$PYTHONPATH"
2. Create Project Structure
bashmkdir voice-llm-system
cd voice-llm-system

# Create directories
mkdir static templates

# Save the HTML file as static/index.html
# Save the Python code as voice_pipeline.py
3. Run the System
bash# Terminal 1: Start your LLM server
cd /Users/kevinsu/baoagent/baoagent-llm-server
./scripts/start_server.sh

# Terminal 2: Start voice pipeline
cd voice-llm-system
conda activate voice-llm
export PYTHONPATH="/Users/kevinsu/baoagent/baoagent-llm-client:$PYTHONPATH"
python voice_pipeline.py
4. Access the System
Open browser to: http://localhost:8000/static/index.html
Mac Mini 16GB Optimizations
Memory Management

Whisper: Use "base" model (74MB) instead of "large" (1550MB)
edge-tts: Lightweight, no local model storage needed
LLM: Configure baoagent server with 7B parameter models

Performance Settings
python# Add to voice_pipeline.py
import torch
import os

# Mac-specific optimizations
if torch.backends.mps.is_available():
    os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
    print("Using Apple Silicon MPS acceleration")

# Memory management
torch.set_num_threads(4)  # Optimize for Mac Mini CPU cores
Key Benefits of This Updated Solution

No Asterisk dependency: Uses pure WebRTC in browser
Mac-compatible packages: All packages work on modern macOS
Apple Silicon optimized: Uses MPS acceleration where available
Simpler architecture: Fewer moving parts, easier to debug
Better performance: Optimized for Mac Mini's capabilities
No external dependencies: Everything runs locally

This updated implementation removes the problematic Asterisk dependency and uses reliable, Mac-compatible packages while maintaining all the functionality of a voice-to-LLM phone system.