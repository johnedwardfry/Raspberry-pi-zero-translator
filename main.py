import configparser
import sys
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import textwrap
import threading
import logging

# --- Platform Detection & Conditional Imports ---
is_raspberry_pi = False
try:
    import RPi.GPIO as GPIO

    is_raspberry_pi = True
except (ImportError, RuntimeError):
    pass
import pygame

# --- Hardware & App Config ---
RECORD_BUTTON_PIN = 17
TOGGLE_BUTTON_PIN = 22
SAMPLE_RATE = 44100
TEMP_AUDIO_FILE = "temp_audio.wav"

# --- Shared State Variables ---
app_state = "ready"
display_text = ""
lock = threading.Lock()


# --- Helper Function to Find a Thai-Supporting Font ---
def find_font():
    """Finds a suitable font that supports Thai characters on the system."""
    # Prioritize the bundled font first
    if os.path.exists("NotoSansThai-Regular.ttf"):
        return "NotoSansThai-Regular.ttf"

    font_paths = [
        "/usr/share/fonts/truetype/laksaman/Laksaman.ttf",  # Common on Raspberry Pi OS
        "C:/Windows/Fonts/leelawadee.ttf",  # Common on Windows
        "C:/Windows/Fonts/leela.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            print(f"INFO: Found system font at {path}")
            return path

    print("WARNING: No Thai-supported font found. Using default font.")
    return None  # Fallback to Pygame's default


# --- Configuration Loader ---
config = configparser.ConfigParser()
if not config.read('config.ini'):
    sys.exit("❌ Error: config.ini file not found.")
try:
    GEMINI_MODEL_NAME = config.get('gemini_settings', 'gemini_model')
    TARGET_DIALECT = config.get('gemini_settings', 'target_dialect')
except Exception as e:
    sys.exit(f"❌ Error reading config.ini: {e}")


# --- Backend API and Logic Functions ---
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
    """Detects if the text is primarily English or Thai."""
    # The 'r' prefix prevents unicode errors on some systems
    return 'thai' if any(r'\u0E00' <= char <= r'\u0E7F' for char in text) else 'english'


def speak_text(text, lang='th'):
    """Generates speech from text and plays it."""
    from gtts import gTTS
    TTS_FILE = "response.mp3"
    try:
        print(f"--- Generating speech for: {text} ---")
        tts = gTTS(text=text, lang=lang)
        tts.save(TTS_FILE)

        pygame.mixer.music.load(TTS_FILE)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    except Exception as e:
        print(f"Error in text-to-speech: {e}")
    finally:
        pygame.mixer.music.unload()
        if os.path.exists(TTS_FILE):
            os.remove(TTS_FILE)


# --- The Main Worker Thread Function ---
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
                is_still_pressed = not GPIO.input(RECORD_BUTTON_PIN)
            else:
                pygame.event.pump()  # Keep pygame responsive
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

    if not recorded_chunks or len(recorded_chunks) < 10:  # Filter out very short, accidental presses
        print("No significant audio recorded.")
        with lock:
            app_state = "ready"
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

        logging.info(f"Source ({source_language}): {source_text} | Translated ({target_lang}): {translated_text}")

        with lock:
            display_text = translated_text
            app_state = "result"

        if target_lang == 'thai':
            speak_text(translated_text, lang='th')

    except Exception as e:
        logging.error(f"Error in worker thread: {e}")
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

    logging.basicConfig(
        filename='translator.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("--- Translator Application Started ---")

    pygame.init()
    pygame.mixer.init()

    fullscreen = True
    if is_raspberry_pi:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RECORD_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(TOGGLE_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Audio Translator")

    font_path = find_font()
    try:
        font_large = pygame.font.Font(font_path, 52)
        font_small = pygame.font.Font(font_path, 24)
    except Exception:
        print("Error loading custom font, using default.")
        font_large = pygame.font.Font(None, 52)
        font_small = pygame.font.Font(None, 24)

    clock = pygame.time.Clock()
    prev_toggle_state = False

    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

            if not is_raspberry_pi and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((1280, 720))

        # --- Pi Toggle Logic ---
        if is_raspberry_pi:
            toggle_state = not GPIO.input(TOGGLE_BUTTON_PIN)
            if toggle_state and not prev_toggle_state:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((1280, 720))
            prev_toggle_state = toggle_state

        # --- Main Trigger Logic ---
        with lock:
            current_state = app_state
        keys = pygame.key.get_pressed()
        record_triggered = (not GPIO.input(RECORD_BUTTON_PIN)) if is_raspberry_pi else (
                    keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

        if current_state == "ready" and record_triggered:
            worker = threading.Thread(target=translation_worker)
            worker.start()

        if current_state == "result" and record_triggered:
            pygame.time.wait(200)
            with lock: app_state = "ready"

        # --- Drawing to the Screen ---
        screen.fill((20, 20, 30))

        if current_state == "ready":
            status_surface = font_large.render("Ready", True, (100, 255, 100))
            instruction_surface = font_small.render("Hold Button or Shift to Record", True, (200, 200, 200))
            screen.blit(status_surface,
                        status_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 40)))
            screen.blit(instruction_surface,
                        instruction_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 40)))
        elif current_state == "recording":
            status_surface = font_large.render("Recording...", True, (255, 80, 80))
            screen.blit(status_surface,
                        status_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2)))
        elif current_state == "processing":
            status_surface = font_large.render("Processing...", True, (255, 255, 100))
            screen.blit(status_surface,
                        status_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2)))
        elif current_state == "result":
            with lock:
                current_text = display_text
            instruction_surface = font_small.render("Press Record Button to Continue", True, (200, 200, 200))
            screen.blit(instruction_surface,
                        instruction_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40)))

            wrapped_text = textwrap.wrap(current_text, width=28)
            y_offset = (screen.get_height() // 2) - (len(wrapped_text) * (font_large.get_height() - 20) / 2)
            for line in wrapped_text:
                result_surface = font_large.render(line, True, (100, 200, 255))
                screen.blit(result_surface, result_surface.get_rect(center=(screen.get_width() // 2, y_offset)))
                y_offset += font_large.get_height()

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    if is_raspberry_pi:
        GPIO.cleanup()


if __name__ == "__main__":
    main()