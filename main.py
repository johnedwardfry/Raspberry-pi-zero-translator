import configparser
import sys
import os
import time
import textwrap
import threading
import logging
import pyaudio
import wave

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
ACTION_BUTTON_PIN = 22
SAMPLE_RATE = 16000
TEMP_AUDIO_FILE = "temp_audio.wav"
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1

# --- Shared State Variables ---
app_state = "ready"
display_text = ""
lock = threading.Lock()

# --- UI Text and Dialect Management ---
STATUS_TEXTS = {
    'ready': {'en': "Ready", 'th': "พร้อม"},
    'recording': {'en': "Recording...", 'th': "กำลังบันทึก..."},
    'processing': {'en': "Processing...", 'th': "กำลังประมวลผล..."}
}
DIALECTS = ['northern', 'southern', 'none']
DIALECT_NAMES = {
    'northern': {'en': 'Northern', 'th': 'เหนือ'},
    'southern': {'en': 'Southern', 'th': 'ใต้'},
    'none': {'en': 'Standard', 'th': 'กลาง'}
}


# --- Helper Function to Find a Thai-Supporting Font ---
def find_font():
    if os.path.exists("NotoSansThai-Regular.ttf"): return "NotoSansThai-Regular.ttf"
    font_paths = ["/usr/share/fonts/truetype/laksaman/Laksaman.ttf", "C:/Windows/Fonts/leelawadee.ttf",
                  "C:/Windows/Fonts/leela.ttf"]
    for path in font_paths:
        if os.path.exists(path): print(f"INFO: Found system font at {path}"); return path
    print("WARNING: No Thai-supported font found. Using default font.");
    return None


# --- Configuration Loader ---
config = configparser.ConfigParser();
config.read('config.ini')
GEMINI_MODEL_NAME = config.get('gemini_settings', 'gemini_model')
INITIAL_DIALECT = config.get('gemini_settings', 'target_dialect', fallback='northern')


# --- Backend API and Logic Functions ---
def configure_gemini():
    import google.generativeai as genai;
    genai.configure(api_key=config.get('secrets', 'google_api_key'));
    return genai


def detect_language(text: str) -> str:
    return 'thai' if any(0x0E00 <= ord(c) <= 0x0E7F for c in text) else 'english'


def speak_text(text, lang='th'):
    from gtts import gTTS
    TTS_FILE = "response.mp3"
    try:
        tts = gTTS(text=text, lang=lang);
        tts.save(TTS_FILE)
        if not pygame.mixer.get_init(): pygame.mixer.init()
        pygame.mixer.music.load(TTS_FILE);
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy(): pygame.time.wait(100)
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
    finally:
        try:
            pygame.mixer.music.unload()
        except Exception:
            pass
        if os.path.exists(TTS_FILE): os.remove(TTS_FILE)


# --- The Main Worker Thread Function (Corrected) ---
def translation_worker(dialect_to_use):
    global app_state, display_text
    with lock:
        app_state = "recording"

    audio_frames = [];
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK)
        is_still_pressed = True
        while is_still_pressed:
            if is_raspberry_pi:
                is_still_pressed = not GPIO.input(RECORD_BUTTON_PIN)
            else:
                pygame.event.pump(); is_still_pressed = pygame.key.get_pressed()[pygame.K_LSHIFT] or \
                                                        pygame.key.get_pressed()[pygame.K_RSHIFT]
            data = stream.read(CHUNK, exception_on_overflow=False);
            audio_frames.append(data)
        stream.stop_stream();
        stream.close();
        p.terminate()
    except Exception as e:
        # --- THIS BLOCK IS THE FIX ---
        print(f"Audio recording error: {e}")
        p.terminate()
        with lock:
            app_state = "ready"
        return
        # --- END OF FIX ---

    if not audio_frames or len(audio_frames) < int(SAMPLE_RATE / CHUNK * 0.2):
        print("No significant audio recorded.");
        with lock: app_state = "ready"
        return

    with wave.open(TEMP_AUDIO_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS);
        wf.setsampwidth(p.get_sample_size(FORMAT));
        wf.setframerate(SAMPLE_RATE);
        wf.writeframes(b''.join(audio_frames))

    with lock:
        app_state = "processing"

    try:
        genai = configure_gemini()
        audio_file = genai.upload_file(path=TEMP_AUDIO_FILE)
        model = genai.GenerativeModel(model_name=GEMINI_MODEL_NAME)

        if dialect_to_use == "none":
            dialect_prompt = "standard Thai"
        else:
            dialect_prompt = f"Northern Thai (Lanna)" if dialect_to_use == "northern" else f"Southern Thai (Pak Tai)"

        prompt = (
            f"Transcribe this audio file. The audio could be in English or Thai. If the transcribed text is English, translate it to {dialect_prompt}. If it is Thai, translate it to English. Your response must contain ONLY the final translated text.")
        response = model.generate_content([prompt, audio_file])
        translated_text = response.text.strip()

        result_language = detect_language(translated_text)
        source_language = 'english' if result_language == 'thai' else 'thai'
        logging.info(f"Source ({source_language}) | Translated ({result_language}): {translated_text}")
        with lock:
            display_text = translated_text; app_state = "result"

    except Exception as e:
        logging.error(f"Error in worker thread: {e}");
        print(f"Error in worker thread: {e}")
        with lock:
            display_text = "An error occurred."; app_state = "result"
    finally:
        if os.path.exists(TEMP_AUDIO_FILE): os.remove(TEMP_AUDIO_FILE)


# --- Main GUI Application ---
def main():
    global app_state, display_text
    logging.basicConfig(filename='translator.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("--- Translator Application Started ---")

    pygame.init()

    if is_raspberry_pi:
        GPIO.setwarnings(False);
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RECORD_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ACTION_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Audio Translator")
    font_path = find_font()
    try:
        font_large = pygame.font.Font(font_path, 52);
        font_small = pygame.font.Font(font_path, 24)
    except Exception:
        print("Error loading custom font, using default.");
        font_large = pygame.font.Font(None, 52);
        font_small = pygame.font.Font(None, 24)

    clock = pygame.time.Clock()

    try:
        current_dialect_index = DIALECTS.index(INITIAL_DIALECT)
    except ValueError:
        current_dialect_index = 0
    action_click_count = 0;
    last_action_click_time = 0;
    prev_action_state = False;
    result_display_start_time = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE): running = False
            if not is_raspberry_pi and event.type == pygame.KEYDOWN and (
                    event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER):
                current_time = time.time()
                if (current_time - last_action_click_time) > 2:
                    action_click_count = 1
                else:
                    action_click_count += 1
                last_action_click_time = current_time
                if action_click_count >= 3:
                    current_dialect_index = (current_dialect_index + 1) % len(DIALECTS);
                    action_click_count = 0

        if is_raspberry_pi:
            action_state = not GPIO.input(ACTION_BUTTON_PIN)
            if action_state and not prev_action_state:
                current_time = time.time()
                if (current_time - last_action_click_time) > 2:
                    action_click_count = 1
                else:
                    action_click_count += 1
                last_action_click_time = current_time
                if action_click_count >= 3:
                    current_dialect_index = (current_dialect_index + 1) % len(DIALECTS);
                    action_click_count = 0
            prev_action_state = action_state

        with lock:
            current_state = app_state; current_text = display_text
        keys = pygame.key.get_pressed()
        record_triggered = (not GPIO.input(RECORD_BUTTON_PIN)) if is_raspberry_pi else (
                    keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

        if current_state == "ready" and record_triggered:
            worker = threading.Thread(target=translation_worker, args=(DIALECTS[current_dialect_index],));
            worker.start()

        if current_state == "result" and record_triggered:
            pygame.time.wait(200);
            with lock: app_state = "ready"

        screen.fill((20, 20, 30))

        active_dialect_name = DIALECT_NAMES[DIALECTS[current_dialect_index]]

        if current_state == "ready":
            status_th = STATUS_TEXTS['ready']['th'];
            status_en = STATUS_TEXTS['ready']['en']
            dialect_th = f"ภาษา: {active_dialect_name['th']}";
            dialect_en = f"Dialect: {active_dialect_name['en']}"
            screen.blit(font_large.render(status_th, True, (100, 255, 100)),
                        font_large.render(status_th, True, (0, 0, 0)).get_rect(
                            center=(screen.get_width() // 2, screen.get_height() // 2 - 80)))
            screen.blit(font_small.render(status_en, True, (200, 200, 200)),
                        font_small.render(status_en, True, (0, 0, 0)).get_rect(
                            center=(screen.get_width() // 2, screen.get_height() // 2 - 30)))
            screen.blit(font_small.render(dialect_th, True, (200, 200, 200)),
                        font_small.render(dialect_th, True, (0, 0, 0)).get_rect(
                            center=(screen.get_width() // 2, screen.get_height() // 2 + 30)))
            screen.blit(font_small.render(dialect_en, True, (200, 200, 200)),
                        font_small.render(dialect_en, True, (0, 0, 0)).get_rect(
                            center=(screen.get_width() // 2, screen.get_height() // 2 + 60)))
        elif current_state in ["recording", "processing"]:
            status_th = STATUS_TEXTS[current_state]['th'];
            status_en = STATUS_TEXTS[current_state]['en']
            color = (255, 80, 80) if current_state == "recording" else (255, 255, 100)
            screen.blit(font_large.render(status_th, True, color),
                        font_large.render(status_th, True, (0, 0, 0)).get_rect(
                            center=(screen.get_width() // 2, screen.get_height() // 2 - 20)))
            screen.blit(font_small.render(status_en, True, (200, 200, 200)),
                        font_small.render(status_en, True, (0, 0, 0)).get_rect(
                            center=(screen.get_width() // 2, screen.get_height() // 2 + 40)))
        elif current_state == "result":
            if result_display_start_time == 0:
                result_display_start_time = pygame.time.get_ticks()
                lang_code = 'th' if detect_language(current_text) == 'thai' else 'en'
                print(f"TTS speaking in {lang_code}: {current_text[:60]}...")
                tts_thread = threading.Thread(target=speak_text, args=(current_text, lang_code));
                tts_thread.start()
            instruction_surface = font_small.render("Press Record Button to Continue", True, (200, 200, 200));
            screen.blit(instruction_surface,
                        instruction_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40)))
            wrapped_text = textwrap.wrap(current_text, width=28)
            y_offset = (screen.get_height() // 2) - (len(wrapped_text) * (font_large.get_height() - 20) / 2)
            for line in wrapped_text:
                result_surface = font_large.render(line, True, (100, 200, 255));
                screen.blit(result_surface, result_surface.get_rect(center=(screen.get_width() // 2, y_offset)));
                y_offset += font_large.get_height()

            time_elapsed = pygame.time.get_ticks() - result_display_start_time
            if time_elapsed > 10000 or record_triggered:
                with lock: app_state = "ready"; result_display_start_time = 0

        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
    if is_raspberry_pi: GPIO.cleanup()



if __name__ == "__main__":
    main()