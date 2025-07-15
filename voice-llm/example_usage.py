#!/usr/bin/env python3
"""
BaoAgent Service Usage Examples
Simple examples of how to use the service directly.
"""

from baoagent_client import BaoAgentClient
import soundfile as sf
import numpy as np

def basic_usage():
    """Basic STT and TTS usage."""
    print("=== Basic Usage Example ===")
    
    with BaoAgentClient() as client:
        # Text-to-Speech
        text = "Hello, this is a test of the BaoAgent service."
        print(f"Generating speech for: '{text}'")
        
        audio_data = client.text_to_speech(text)
        if audio_data is not None:
            client.save_audio(audio_data, "example_output.wav")
            print("✓ TTS completed successfully")
            
            # Speech-to-Text
            print("Transcribing the generated audio...")
            transcription = client.transcribe_audio(audio_data)
            
            if transcription:
                print(f"✓ Transcription: {transcription}")
            else:
                print("✗ Transcription failed")
        else:
            print("✗ TTS failed")

def file_transcription():
    """Transcribe an existing audio file."""
    print("\n=== File Transcription Example ===")
    
    audio_file = "tts_output.wav"  # Use existing file if available
    
    try:
        with BaoAgentClient() as client:
            # Load and prepare audio
            audio_data, sr = sf.read(audio_file)
            
            # Resample if needed
            if sr != 16000:
                import librosa
                audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=16000)
                sr = 16000
            
            # Convert to int16
            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            print(f"Transcribing {audio_file}...")
            transcription = client.transcribe_audio(audio_data, sr)
            
            if transcription:
                print(f"✓ Transcription: {transcription}")
            else:
                print("✗ Transcription failed")
                
    except FileNotFoundError:
        print(f"Audio file {audio_file} not found. Run TTS first to generate audio.")
    except Exception as e:
        print(f"Error: {e}")

def streaming_example():
    """Example of processing audio in chunks (simulating real-time)."""
    print("\n=== Streaming Example ===")
    
    with BaoAgentClient() as client:
        # Generate a longer audio file for streaming demo
        text = "This is a longer text to demonstrate streaming transcription. We will process this audio in chunks to simulate real-time processing."
        
        print("Generating longer audio for streaming demo...")
        audio_data = client.text_to_speech(text)
        
        if audio_data is not None:
            # Process in 1-second chunks
            chunk_size = 24000  # 1 second at 24kHz
            chunks = []
            
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                chunks.append(chunk)
            
            print(f"Processing {len(chunks)} chunks...")
            
            for i, chunk in enumerate(chunks):
                print(f"Chunk {i+1}/{len(chunks)}: ", end="")
                transcription = client.transcribe_audio(chunk)
                if transcription:
                    print(f"'{transcription}'")
                else:
                    print("(silence or no transcription)")

def service_status():
    """Check service status."""
    print("\n=== Service Status ===")
    
    with BaoAgentClient() as client:
        status = client.get_status()
        print(f"STT Model: {'✓ Ready' if status.get('stt_warmed_up') else '✗ Not ready'}")
        print(f"TTS Model: {'✓ Ready' if status.get('tts_warmed_up') else '✗ Not ready'}")

if __name__ == "__main__":
    basic_usage()
    file_transcription()
    streaming_example()
    service_status() 