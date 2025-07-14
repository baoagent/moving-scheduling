## [COMPLETED] Step 1: Implement Mac-Optimized STT in Python
- Implement the MacOptimizedSTT class as described in the README
- Ensure it uses Whisper, numpy, torch, and librosa
- Test with sample audio input

## [COMPLETED] Step 2: Implement Mac-Optimized TTS in Python
- Implement the MacOptimizedTTS class as described in the README
- Ensure it uses edge-tts, asyncio, numpy, wave, tempfile, and os
- Test with sample text input

## [IN PROGRESS] Step 3: Replace MacOptimizedTTS with Moshi TTS (kyutai/tts-1.6b-en_fr)
- Integrate kyutai/tts-1.6b-en_fr (Moshi TTS) using the moshi-mlx package for fast, local TTS
- Update the TTS wrapper to use Moshi TTS instead of edge-tts
- Expose TTS as a FastAPI endpoint for server use
- Test end-to-end voice-to-LLM-to-voice flow with new TTS
