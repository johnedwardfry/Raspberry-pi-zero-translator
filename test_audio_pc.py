import pygame
from gtts import gTTS
import os
import sounddevice as sd

# --- Settings ---
TEST_TEXT = "This is a PC audio test."
FILENAME = "test_audio.mp3"

# --- Main Test ---
try:
    # 1. List all available audio devices
    print("--- Querying Audio Devices ---")
    print(sd.query_devices())
    print("-" * 30)
    print("The '>' symbol indicates your current default output device.")
    print("-" * 30)

    # 2. Generate a test audio file
    print(f"--- Generating test speech: '{TEST_TEXT}' ---")
    tts = gTTS(text=TEST_TEXT, lang='en')
    tts.save(FILENAME)

    # 3. Initialize Pygame and its mixer
    pygame.init()
    pygame.mixer.init()
    print("--- Pygame Mixer Initialized ---")

    # 4. Load and play the audio on the default device
    print(f"--- Playing {FILENAME}... ---")
    pygame.mixer.music.load(FILENAME)
    pygame.mixer.music.play()

    # 5. Wait for playback to finish
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    print("--- ✅ Test complete. ---")

except Exception as e:
    print(f"--- ❌ An error occurred: {e} ---")

finally:
    # 6. Clean up the test file
    if os.path.exists(FILENAME):
        os.remove(FILENAME)
    pygame.quit()