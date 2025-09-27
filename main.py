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
app_state = "ready"
display_text = ""
lock = threading.Lock()


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
    """Translates text using the specified Gemini model and dialect instructions."""
    constraint = "Your response must contain ONLY the translated text and nothing else."

    if target_language == "thai":
        # --- THIS IS THE FIX ---
        # We now check for the 'none' case specifically.
        if dialect == "none":
            prompt = (f"Translate this to standard Thai: '{text}'. {constraint}")
        else:
            prompt = (f"Translate this to {dialect} Thai (e.g., Lanna or Pak Tai): '{text}'. {constraint}")

    elif target_language == "english":
        prompt = (f"Translate this to English: '{text}'. {constraint}")
    else:
        raise ValueError("Unsupported target language.")

    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt)
    return response.text.strip()


def detect_language(text):
    return 'thai' if any('\u0E00' <= char <= '\u0E7F' for char in text) else 'english'


# --- The Main Worker Thread Function (Unchanged) ---
def translation_worker():
    global app_state, display_text
    with lock:
        app_state = "recording"
    recorded_chunks = []
    try:
        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1)
        stream.start()
        is_still_pressed = True
        while is_still_pressed:
            if is_raspberry_pi:
                is_still_pressed = not GPIO.input(BUTTON_PIN)
            else:
                is_still_pressed = pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[
                    pygame.K_RSHIFT]
            data, _ = stream.read(1024)
            recorded_chunks.append(data)
        stream.stop()
    except Exception as e:
        print(f"Audio recording error: {e}")
        with lock:
            app_state = "ready"
        return
    if not recorded_chunks:
        with lock: app_state = "ready"
        return
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


# --- Main GUI Application (Updated) ---
def main():
    global app_state, display_text

    pygame.init()
    if is_raspberry_pi:
        GPIO.setwarnings(False);
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    screen = pygame.display.set_mode((800, 480))
    pygame.display.set_caption("Audio Translator")

    # --- Font Loading: Load the bundled Noto Sans Thai font ---
    try:
        font_path = "NotoSansThai-Regular.ttf"
        font_large = pygame.font.Font(font_path, 52)
        font_small = pygame.font.Font(font_path, 24)
    except FileNotFoundError:
        print("WARNING: NotoSansThai-Regular.ttf not found. Falling back to default font.")
        # Fallback if the font file is missing
        font_large = pygame.font.Font(None, 52)
        font_small = pygame.font.Font(None, 24)

    clock = pygame.time.Clock()

    running = True
    while running:
        # --- Event Handling (for quitting) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        # --- Read shared state from the worker thread ---
        with lock:
            current_state = app_state;
            current_text = display_text

        # --- Check for input triggers based on the current state ---
        keys = pygame.key.get_pressed()
        is_triggered = (not GPIO.input(BUTTON_PIN)) if is_raspberry_pi else (
                    keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

        if current_state == "ready" and is_triggered:
            worker = threading.Thread(target=translation_worker)
            worker.start()

        # --- CONTROL FLOW FIX: Check for a press during the "result" state ---
        if current_state == "result" and is_triggered:
            # Add a small delay to prevent accidental double-presses
            pygame.time.wait(200)
            with lock:
                app_state = "ready"

        # --- Drawing to the Screen ---
        screen.fill((20, 20, 30))

        if current_state == "ready":
            status_surface = font_large.render("Ready", True, (100, 255, 100))
            instruction_surface = font_small.render("Hold Button or Shift to Record", True, (200, 200, 200))
            screen.blit(status_surface, status_surface.get_rect(center=(400, 200)))
            screen.blit(instruction_surface, instruction_surface.get_rect(center=(400, 280)))
        elif current_state == "recording":
            status_surface = font_large.render("Recording...", True, (255, 80, 80))
            screen.blit(status_surface, status_surface.get_rect(center=(400, 240)))
        elif current_state == "processing":
            status_surface = font_large.render("Processing...", True, (255, 255, 100))
            screen.blit(status_surface, status_surface.get_rect(center=(400, 240)))
        elif current_state == "result":
            instruction_surface = font_small.render("Press again to continue", True, (200, 200, 200))
            screen.blit(instruction_surface, instruction_surface.get_rect(center=(400, 440)))

            wrapped_text = textwrap.wrap(current_text, width=28)
            y_offset = 240 - (len(wrapped_text) * 35)
            for line in wrapped_text:
                result_surface = font_large.render(line, True, (100, 200, 255))
                screen.blit(result_surface, result_surface.get_rect(center=(400, y_offset)))
                y_offset += 70

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    if is_raspberry_pi:
        GPIO.cleanup()


if __name__ == "__main__":
    main()