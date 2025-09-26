import configparser
import google.generativeai as genai
import sys

# --- Configuration Loader ---
config = configparser.ConfigParser()
if not config.read('config.ini'):
    # This error will still print to the console if the config is missing, which is good.
    print("❌ Error: config.ini file not found.", file=sys.stderr)
    sys.exit(1)

try:
    GEMINI_MODEL_NAME = config.get('gemini_settings', 'gemini_model')
    TARGET_DIALECT = config.get('gemini_settings', 'target_dialect')
    GEMINI_API_KEY = config.get('secrets', 'google_api_key')
    genai.configure(api_key=GEMINI_API_KEY)
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"❌ Error reading config.ini: {e}", file=sys.stderr)
    sys.exit(1)


# --- Main Translation Function ---
def translate_with_gemini(text, dialect, model_name):
    """Translates text using the specified Gemini model and dialect instructions."""
    # The print statements that were here have been removed.

    constraint = (
        "Your response must contain ONLY the translated Thai text and nothing else. "
        "Do not add explanations, formatting, or any extra characters."
    )

    if dialect == "northern":
        prompt = (f"Translate the following English text into Northern Thai (Lanna dialect). {constraint}\n\n"
                  f"English: '{text}'")
    elif dialect == "southern":
        prompt = (f"Translate the following English text into Southern Thai (Pak Tai dialect). {constraint}\n\n"
                  f"English: '{text}'")
    else:
        prompt = (f"Translate the following English text into standard Thai. {constraint}\n\n"
                  f"English: '{text}'")

    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text.strip()


# --- Main Execution Logic ---
if __name__ == "__main__":
    sample_text = "The food is very delicious! Where can I buy a motorcycle?"

    try:
        translated_text = translate_with_gemini(sample_text, TARGET_DIALECT.lower(), GEMINI_MODEL_NAME)

        # This now prints ONLY the final translated text to the standard output.
        print(translated_text)

    except Exception as e:
        # Errors will be printed to the standard error stream.
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)