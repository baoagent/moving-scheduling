#!/usr/bin/env python3
"""
BaoAgent Service - Persistent STT and TTS Service
Keeps both models loaded in memory to avoid warmup delays.
"""

import subprocess
import tempfile
import os
import soundfile as sf
import numpy as np
import time
import json
import sys
from pathlib import Path

class BaoAgentService:
    def __init__(self):
        self.stt_warmed_up = False
        self.tts_warmed_up = False
        self.stt_model_repo = "kyutai/stt-2.6b-en-mlx"
        
    def warmup_stt(self):
        """Warm up the STT model with a dummy inference."""
        if not self.stt_warmed_up:
            print("Warming up STT model...")
            try:
                # Create a dummy audio file (1 second of silence)
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    silence = np.zeros(16000, dtype=np.int16)  # 1 second of silence at 16kHz
                    sf.write(tmp_file.name, silence, 16000)
                    dummy_audio_path = tmp_file.name
                
                # Run dummy inference to warm up
                result = subprocess.run(
                    [
                        "python", "-m", "moshi_mlx.run_inference",
                        "--hf-repo", self.stt_model_repo,
                        dummy_audio_path, "--temp", "0"
                    ],
                    capture_output=True, text=True, timeout=120
                )
                os.unlink(dummy_audio_path)
                self.stt_warmed_up = True
                print("STT model warmed up successfully!")
            except Exception as e:
                print(f"STT warmup failed: {e}")
                return False
        return True
    
    def warmup_tts(self):
        """Warm up the TTS model with a dummy inference."""
        if not self.tts_warmed_up:
            print("Warming up TTS model...")
            print(f"Using TTS script: delayed-streams-modeling/scripts/tts_mlx.py")
            try:
                # Create a dummy text file
                with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
                    tf.write("Hello")
                    tf.flush()
                    text_path = tf.name
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    output_path = tmp_file.name
                
                # Build the command using the tts_mlx.py script
                cmd = [
                    "python3", "delayed-streams-modeling/scripts/tts_mlx.py",
                    text_path, output_path, "--quantize", "8"
                ]
                print(f"Executing TTS command: {' '.join(cmd)}")
                
                # Run dummy inference to warm up
                result = subprocess.run(cmd, check=True, timeout=120, capture_output=True, text=True)
                
                print("TTS warmup command completed successfully")
                print(f"TTS stdout: {result.stdout}")
                
                os.unlink(text_path)
                os.unlink(output_path)
                self.tts_warmed_up = True
                print("TTS model warmed up successfully!")
            except subprocess.CalledProcessError as e:
                print(f"TTS warmup failed: {e}")
                print(f"TTS stderr: {e.stderr}")
                print(f"TTS stdout: {e.stdout}")
                print("Continuing without TTS functionality...")
                return False
            except Exception as e:
                print(f"TTS warmup failed: {e}")
                print("Continuing without TTS functionality...")
                return False
        return True
    
    def transcribe_audio(self, audio_data, sample_rate=16000):
        """Transcribe audio using the warmed up STT model."""
        if not self.stt_warmed_up:
            if not self.warmup_stt():
                return None
        
        # Save audio to a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate)
            audio_path = tmp_file.name
        
        try:
            # Run the STT model
            result = subprocess.run(
                [
                    "python", "-m", "moshi_mlx.run_inference",
                    "--hf-repo", self.stt_model_repo,
                    audio_path, "--temp", "0"
                ],
                capture_output=True, text=True, check=True, timeout=60
            )
            
            # Extract only the transcription text from stdout
            stdout_lines = result.stdout.strip().split('\n')
            transcription = ""
            
            # Look for the actual transcription (usually the last line that's not debug info)
            for line in reversed(stdout_lines):
                line = line.strip()
                # Skip lines that are clearly debug info
                if (line.startswith('Info:') or 
                    line.startswith('{') or 
                    line.startswith('}') or
                    'card' in line or
                    'dim' in line or
                    'num_heads' in line or
                    'model_id' in line or
                    'tokenizer' in line or
                    'steps' in line or
                    'token per sec' in line):
                    continue
                # If we find a line that looks like transcription, use it
                if line and not line.startswith('Info:') and not line.startswith('{'):
                    transcription = line
                    break
            
            return transcription
        except subprocess.TimeoutExpired:
            print("STT inference timed out")
            return None
        except Exception as e:
            print(f"STT inference failed: {e}")
            return None
        finally:
            os.unlink(audio_path)
    
    def text_to_speech(self, text):
        """Generate speech from text using the warmed up TTS model."""
        if not self.tts_warmed_up:
            if not self.warmup_tts():
                return None
        
        print(f"Generating TTS for text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        # Save text to temporary file
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
            tf.write(text)
            tf.flush()
            text_path = tf.name
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Build the command using the tts_mlx.py script
            cmd = [
                "python3", "delayed-streams-modeling/scripts/tts_mlx.py",
                text_path, output_path, "--quantize", "8"
            ]
            print(f"Executing TTS inference command: {' '.join(cmd)}")
            
            # Run the TTS model
            result = subprocess.run(cmd, check=True, timeout=60, capture_output=True, text=True)
            
            print("TTS inference command completed successfully")
            print(f"TTS inference stdout: {result.stdout}")
            
            # Read the generated audio
            audio_data, _ = sf.read(output_path, dtype='int16')
            print(f"Generated audio with {len(audio_data)} samples")
            return audio_data
        except subprocess.CalledProcessError as e:
            print(f"TTS inference failed: {e}")
            print(f"TTS inference stderr: {e.stderr}")
            print(f"TTS inference stdout: {e.stdout}")
            return None
        except subprocess.TimeoutExpired:
            print("TTS inference timed out")
            return None
        except Exception as e:
            print(f"TTS inference failed: {e}")
            return None
        finally:
            os.unlink(text_path)
            os.unlink(output_path)
    
    def process_command(self, command_data):
        """Process a JSON command and return the result."""
        try:
            command = json.loads(command_data)
            cmd_type = command.get('type')
            
            if cmd_type == 'transcribe':
                # Expect base64 encoded audio data
                import base64
                audio_b64 = command.get('audio_data')
                sample_rate = command.get('sample_rate', 16000)
                
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                    transcription = self.transcribe_audio(audio_data, sample_rate)
                    return json.dumps({
                        'type': 'transcription_result',
                        'text': transcription,
                        'success': transcription is not None
                    })
            
            elif cmd_type == 'tts':
                text = command.get('text', '')
                audio_data = self.text_to_speech(text)
                
                if audio_data is not None:
                    import base64
                    audio_bytes = audio_data.tobytes()
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                    return json.dumps({
                        'type': 'tts_result',
                        'audio_data': audio_b64,
                        'sample_rate': 24000,  # TTS default
                        'success': True
                    })
                else:
                    return json.dumps({
                        'type': 'tts_result',
                        'success': False,
                        'error': 'TTS generation failed'
                    })
            
            elif cmd_type == 'status':
                return json.dumps({
                    'type': 'status',
                    'stt_warmed_up': self.stt_warmed_up,
                    'tts_warmed_up': self.tts_warmed_up
                })
            
            else:
                return json.dumps({
                    'type': 'error',
                    'error': f'Unknown command type: {cmd_type}'
                })
                
        except Exception as e:
            return json.dumps({
                'type': 'error',
                'error': str(e)
            })

    def debug_tts_models(self):
        """Debug method to test the TTS script."""
        print("\n=== TTS Script Debug ===")
        
        try:
            # Create a dummy text file
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
                tf.write("Hello")
                tf.flush()
                text_path = tf.name
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Test the tts_mlx.py script
            cmd = [
                "python3", "delayed-streams-modeling/scripts/tts_mlx.py",
                text_path, output_path, "--quantize", "8"
            ]
            print(f"Testing command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✓ TTS script - SUCCESS")
                if os.path.exists(output_path):
                    print(f"  Generated audio file: {output_path}")
            else:
                print(f"✗ TTS script - FAILED")
                print(f"  Return code: {result.returncode}")
                print(f"  Stderr: {result.stderr[:200]}...")
            
            # Cleanup
            os.unlink(text_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
                
        except Exception as e:
            print(f"✗ TTS script - ERROR: {e}")
        
        print("\n=== TTS Debug Complete ===")

def main():
    """Main service loop."""
    service = BaoAgentService()
    
    print("BaoAgent Service starting...")
    print("Commands: transcribe, tts, status, quit")
    
    # Debug TTS models first
    service.debug_tts_models()
    
    # Warm up both models on startup
    print("Warming up models...")
    service.warmup_stt()
    service.warmup_tts()
    print("Service ready!")
    
    while True:
        try:
            # Read command from stdin
            command_line = input().strip()
            
            if command_line.lower() == 'quit':
                print("Shutting down service...")
                break
            
            # Process the command
            result = service.process_command(command_line)
            print(result)
            
        except EOFError:
            print("EOF received, shutting down...")
            break
        except KeyboardInterrupt:
            print("Interrupted, shutting down...")
            break
        except Exception as e:
            print(json.dumps({
                'type': 'error',
                'error': f'Service error: {str(e)}'
            }))

if __name__ == "__main__":
    main() 