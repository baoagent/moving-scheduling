#!/usr/bin/env python3
"""
Comprehensive Test script for BaoAgent Service
Demonstrates persistent STT and TTS with no warmup delays after initial load,
direct service usage, and streaming capabilities.
"""

from baoagent_client import BaoAgentClient
import soundfile as sf
import numpy as np
import time
import os
import sys
import argparse

def test_persistent_service():
    """Test the BaoAgent service with persistent behavior and warmup performance."""
    
    print("=== BaoAgent Persistent Service Test ===")
    print("This will demonstrate persistent STT and TTS with no warmup delays.")
    
    # Use context manager to automatically start/stop service
    with BaoAgentClient() as client:
        print("\n1. Testing TTS (first call - may be slow due to warmup)...")
        start_time = time.time()
        
        text1 = "Hello, this is the first test of the BaoAgent service."
        audio1 = client.text_to_speech(text1)
        
        if audio1 is not None:
            client.save_audio(audio1, "test1_output.wav")
            print(f"TTS completed in {time.time() - start_time:.2f} seconds")
            print(f"Audio length: {len(audio1) / 24000:.2f} seconds")
            
            print("\n2. Testing STT with the generated audio...")
            start_time = time.time()
            transcription1 = client.transcribe_audio(audio1)
            print(f"STT completed in {time.time() - start_time:.2f} seconds")
            
            if transcription1:
                print(f"Original: {text1}")
                print(f"Transcribed: {transcription1}")
        
        print("\n3. Testing TTS again (should be fast now)...")
        start_time = time.time()
        
        text2 = "This is the second test. The model should already be warmed up."
        audio2 = client.text_to_speech(text2)
        
        if audio2 is not None:
            client.save_audio(audio2, "test2_output.wav")
            print(f"TTS completed in {time.time() - start_time:.2f} seconds")
            print(f"Audio length: {len(audio2) / 24000:.2f} seconds")
            
            print("\n4. Testing STT again (should be fast)...")
            start_time = time.time()
            transcription2 = client.transcribe_audio(audio2)
            print(f"STT completed in {time.time() - start_time:.2f} seconds")
            
            if transcription2:
                print(f"Original: {text2}")
                print(f"Transcribed: {transcription2}")
        
        print("\n5. Testing with existing audio file...")
        try:
            # Try to load and transcribe an existing audio file
            audio_file = "tts_output.wav"
            if os.path.exists(audio_file):
                audio_data, sr = sf.read(audio_file)
                if sr != 16000:
                    import librosa
                    audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=16000)
                    sr = 16000
                
                if audio_data.dtype != np.int16:
                    audio_data = (audio_data * 32767).astype(np.int16)
                
                start_time = time.time()
                transcription3 = client.transcribe_audio(audio_data, sr)
                print(f"File transcription completed in {time.time() - start_time:.2f} seconds")
                
                if transcription3:
                    print(f"File transcription: {transcription3}")
            else:
                print(f"Audio file {audio_file} not found, skipping file test.")
        except Exception as e:
            print(f"File transcription failed: {e}")
        
        print("\n6. Service status:")
        status = client.get_status()
        print(f"STT warmed up: {status.get('stt_warmed_up', False)}")
        print(f"TTS warmed up: {status.get('tts_warmed_up', False)}")
        
        print("\n=== Persistent Service Test Complete ===")
        print("Notice how subsequent calls are much faster after the initial warmup!")

def test_direct_service():
    """Test the BaoAgent service with direct usage patterns."""
    
    print("\n=== Direct BaoAgent Service Test ===")
    print("Testing STT and TTS with direct service usage...")
    
    with BaoAgentClient() as client:
        print("\n1. Testing TTS...")
        start_time = time.time()
        
        text = "Hello, this is a test of the direct BaoAgent service."
        audio_data = client.text_to_speech(text)
        
        if audio_data is not None:
            client.save_audio(audio_data, "direct_test_output.wav")
            print(f"TTS completed in {time.time() - start_time:.2f} seconds")
            print(f"Audio length: {len(audio_data) / 24000:.2f} seconds")
            
            print("\n2. Testing STT with the generated audio...")
            start_time = time.time()
            transcription = client.transcribe_audio(audio_data)
            print(f"STT completed in {time.time() - start_time:.2f} seconds")
            
            if transcription:
                print(f"Original text: {text}")
                print(f"Transcription: {transcription}")
            else:
                print("STT failed")
        else:
            print("TTS failed")
        
        print("\n3. Testing STT with existing audio file...")
        try:
            audio_file = "tts_output.wav"
            if os.path.exists(audio_file):
                audio_data, sr = sf.read(audio_file)
                if sr != 16000:
                    import librosa
                    audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=16000)
                    sr = 16000
                
                if audio_data.dtype != np.int16:
                    audio_data = (audio_data * 32767).astype(np.int16)
                
                start_time = time.time()
                transcription = client.transcribe_audio(audio_data, sr)
                print(f"File transcription completed in {time.time() - start_time:.2f} seconds")
                
                if transcription:
                    print(f"File transcription: {transcription}")
            else:
                print(f"Audio file {audio_file} not found, skipping file test.")
        except Exception as e:
            print(f"File transcription failed: {e}")
        
        print("\n4. Service status:")
        status = client.get_status()
        print(f"STT warmed up: {status.get('stt_warmed_up', False)}")
        print(f"TTS warmed up: {status.get('tts_warmed_up', False)}")
        
        print("\n=== Direct Service Test Complete ===")
        print("Direct service usage is much cleaner!")

def test_streaming_stt():
    """Test streaming STT functionality."""
    print("\n=== Streaming STT Test ===")
    
    with BaoAgentClient() as client:
        # Load audio file
        audio_file = "tts_output.wav"
        if not os.path.exists(audio_file):
            print(f"Audio file {audio_file} not found, skipping streaming test.")
            return
        
        audio_data, sr = sf.read(audio_file)
        if sr != 16000:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=16000)
            sr = 16000
        
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Simulate streaming by processing in chunks
        chunk_size = 16000  # 1 second chunks
        print(f"Processing {len(audio_data)} samples in {chunk_size}-sample chunks...")
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            if len(chunk) == chunk_size:  # Only process full chunks
                print(f"Processing chunk {i//chunk_size + 1}...")
                transcription = client.transcribe_audio(chunk, sr)
                if transcription:
                    print(f"  Chunk {i//chunk_size + 1}: {transcription}")
        
        print("\n=== Streaming STT Test Complete ===")

def run_comprehensive_test():
    """Run all comprehensive tests for the BaoAgent service."""
    print("=== Comprehensive BaoAgent Service Test Suite ===")
    print("This test suite covers:")
    print("- Persistent service behavior and warmup performance")
    print("- Direct service usage patterns")
    print("- Streaming STT capabilities")
    print("- File transcription testing")
    print("- Service status monitoring")
    print("=" * 60)
    
    # Run all tests
    test_persistent_service()
    test_direct_service()
    test_streaming_stt()
    
    print("\n=== All Tests Complete ===")
    print("The BaoAgent service has been thoroughly tested!")

def main():
    """Main function to handle command line arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="BaoAgent Service Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_baoagent_service.py                    # Run all tests
  python test_baoagent_service.py --test persistent # Run only persistent service test
  python test_baoagent_service.py --test direct     # Run only direct service test
  python test_baoagent_service.py --test streaming  # Run only streaming STT test
  python test_baoagent_service.py --list            # List available tests
        """
    )
    
    parser.add_argument(
        '--test', 
        choices=['persistent', 'direct', 'streaming', 'all'],
        default='all',
        help='Specific test to run (default: all)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available tests and exit'
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Available tests:")
        print("  persistent - Test persistent service behavior and warmup performance")
        print("  direct     - Test direct service usage patterns")
        print("  streaming  - Test streaming STT functionality")
        print("  all        - Run all tests (default)")
        return
    
    # Run the specified test
    if args.test == 'all':
        run_comprehensive_test()
    elif args.test == 'persistent':
        test_persistent_service()
    elif args.test == 'direct':
        test_direct_service()
    elif args.test == 'streaming':
        test_streaming_stt()

if __name__ == "__main__":
    main() 