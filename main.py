import configparser
import sys
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import textwrap
import threading

# --- Platform Detection & Conditional Imports ---
is_raspberry_pi = False
try:
    import RPi.GPIO as GPIO

    is_raspberry_pi = True
except (ImportError, RuntimeError):
    pass

import pygame

# --- Hardware & App Config ---
BUTTON_PIN = 17
SAMPLE_RATE = 44100
TEMP_AUDIO_FILE = "temp_audio.wav"

# --- Shared State Variables (for threading) ---
app_state = "ready"  # States: ready, recording, processing, result
display_text = ""
lock = threading.Lock()

# --- NEW: Font-finding Helper Function ---
def find_font():
    """Finds a suitable font that supports Thai characters on the system."""
    font_paths = [
        "/usr/share/fonts/truetype/laksaman/Laksaman.ttf",  # Common on Raspberry Pi OS
        "C:/Windows/Fonts/leelawadee.ttf",                  # Common on Windows
        "C:/Windows/Fonts/leela.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            print(f"INFO: Found font at {path}")
            return path
    print("WARNING: No Thai-supported system font found. Using default font.")
    return None # Fallback to Pygame's default

# --- All backend functions are unchanged and are omitted for brevity ---
config = configparser.ConfigParser();
config.read('config.ini')
GEMINI_MODEL_NAME = config.get('gemini_settings', 'gemini_model')
TARGET_DIALECT = config.get('gemini_settings', 'target_dialect')


def configure_gemini():
    import google.generativeai as genai
    genai.configure(api_key=config.get('secrets', 'google_api_key'))
    return genai


def transcribe_audio(genai, file_path, model_name):
    audio_file = genai.upload_file(path=file_path)
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(["Transcribe this audio file.", audio_file])
    return response.text.strip()


def translate_text(genai, text, target_language, dialect, model_name):
    constraint = "Your response must contain ONLY the translated text and nothing else."
    if target_language == "thai":
        prompt = (f"Translate this to {dialect} Thai: '{text}'. {constraint}")
    else:  # English
        prompt = (f"Translate this to English: '{text}'. {constraint}")
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt)
    return response.text.strip()


def detect_language(text):
    return 'thai' if any('\u0E00' <= char <= '\u0E7F' for char in text) else 'english'


# --- The Main Worker Thread Function (CORRECTED) ---
def translation_worker():
    global app_state, display_text

    # === STEP 1: RECORDING IS NOW INSIDE THE THREAD ===
    with lock:
        app_state = "recording"

    recorded_chunks = []
    try:
        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1)
        stream.start()
        while True:
            is_pressed = not GPIO.input(BUTTON_PIN) if is_raspberry_pi else pygame.key.get_pressed()[pygame.K_LSHIFT] or \
                                                                            pygame.key.get_pressed()[pygame.K_RSHIFT]
            if not is_pressed:
                break
            data, _ = stream.read(1024)
            recorded_chunks.append(data)
        stream.stop()
    except Exception as e:
        print(f"Audio recording error: {e}")
        with lock:
            app_state = "ready"
        return

    if not recorded_chunks:
        with lock:
            app_state = "ready"
        return

    # === STEP 2: PROCESSING IS ALSO IN THE THREAD ===
    with lock:
        app_state = "processing"

    try:
        genai = configure_gemini()
        recording = np.concatenate(recorded_chunks, axis=0)
        sf.write(TEMP_AUDIO_FILE, recording, SAMPLE_RATE)

        source_text = transcribe_audio(genai, TEMP_AUDIO_FILE, model_name=GEMINI_MODEL_NAME)
        source_language = detect_language(source_text)

        target_lang = 'thai' if source_language == 'english' else 'english'
        translated_text = translate_text(genai, source_text, target_lang, TARGET_DIALECT.lower(), GEMINI_MODEL_NAME)

        with lock:
            display_text = translated_text
            app_state = "result"

    except Exception as e:
        print(f"Error in worker thread: {e}")
        with lock:
            display_text = "An error occurred."
            app_state = "result"
    finally:
        if os.path.exists(TEMP_AUDIO_FILE):
            os.remove(TEMP_AUDIO_FILE)


# --- Main GUI Application ---
def main():
    global app_state, display_text

    pygame.init()
    if is_raspberry_pi:
        GPIO.setwarnings(False);
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    screen = pygame.display.set_mode((800, 480))
    pygame.display.set_caption("Audio Translator")
    font_large = pygame.font.Font(None, 60)
    font_small = pygame.font.Font(None, 24)
    clock = pygame.time.Clock()

    result_display_start_time = 0  # Timer for the result screen

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        with lock:
            ready_to_start = (app_state == "ready")

        if ready_to_start:
            keys = pygame.key.get_pressed()
            is_triggered = (not GPIO.input(BUTTON_PIN)) if is_raspberry_pi else (
                        keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
            if is_triggered:
                worker = threading.Thread(target=translation_worker)
                worker.start()

        # --- Drawing to the Screen ---
        screen.fill((20, 20, 30))  # Dark blue background

        with lock:
            current_state = app_state;
            current_text = display_text

        if current_state == "ready":
            status_surface = font_large.render("Ready", True, (100, 255, 100))  # Light Green
            instruction_surface = font_small.render("Hold Button or Shift to Record", True, (200, 200, 200))
            screen.blit(status_surface, status_surface.get_rect(center=(400, 200)))
            screen.blit(instruction_surface, instruction_surface.get_rect(center=(400, 280)))
        elif current_state == "recording":
            status_surface = font_large.render("Recording...", True, (255, 80, 80))  # Light Red
            screen.blit(status_surface, status_surface.get_rect(center=(400, 240)))
        elif current_state == "processing":
            status_surface = font_large.render("Processing...", True, (255, 255, 100))  # Light Yellow
            screen.blit(status_surface, status_surface.get_rect(center=(400, 240)))
        elif current_state == "result":
            # === STEP 3: NON-BLOCKING TIMER FOR RESULTS ===
            if result_display_start_time == 0:
                result_display_start_time = pygame.time.get_ticks()

            wrapped_text = textwrap.wrap(current_text, width=30)
            y_offset = 240 - (len(wrapped_text) * 35)  # Center vertically
            for line in wrapped_text:
                result_surface = font_large.render(line, True, (100, 200, 255))  # Light Blue
                screen.blit(result_surface, result_surface.get_rect(center=(400, y_offset)))
                y_offset += 70

            if pygame.time.get_ticks() - result_display_start_time > 5000:  # 5 seconds
                with lock:
                    app_state = "ready"
                result_display_start_time = 0

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    if is_raspberry_pi:
        GPIO.cleanup()


if __name__ == "__main__":
    main()