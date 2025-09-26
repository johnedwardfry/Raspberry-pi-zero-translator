import configparser
import google.generativeai as genai
import sys

# --- Configuration Loader ---
config = configparser.ConfigParser()
# Try to read the config file and handle errors gracefully.
if not config.read('config.ini'):
    print("❌ Error: config.ini file not found.")
    print("   Please copy 'config.ini.example' to 'config.ini' and add your API key.")
    sys.exit(1)

# Load settings from the simplified config file
try:
    GEMINI_MODEL_NAME = config.get('gemini_settings', 'gemini_model')
    TARGET_DIALECT = config.get('gemini_settings', 'target_dialect')
    GEMINI_API_KEY = config.get('secrets', 'google_api_key')

    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        raise ValueError("API key not found in config.ini.")

    # Configure the client with the API key
    genai.configure(api_key=GEMINI_API_KEY)

except (configparser.NoSectionError, configparser.NoOptionError, ValueError) as e:
    print(f"❌ Error reading config.ini: {e}")
    sys.exit(1)


# --- Main Translation Function ---

def translate_with_gemini(text, dialect, model_name):
    """Translates text using the specified Gemini model and dialect instructions."""
    print(f"--- Using Simple Gemini API for '{dialect}' dialect ---")
    print(f"--- Model: {model_name} ---")

    prompt = f"Translate the following English text into Thai: '{text}'"

    if dialect == "northern":
        prompt = (f"Translate the following English text into Thai, using a friendly, informal tone "
                  f"appropriate for the Northern Thai (Lanna) dialect. Emphasize clarity but "
                  f"incorporate common Northern vocabulary if natural.\n\nEnglish: '{text}'")
    elif dialect == "southern":
        prompt = (f"Translate the following English text into Thai, using a direct and clear tone "
                  f"appropriate for the Southern Thai (Pak Tai) dialect. Use common Southern "
                  f"phrasing where it fits naturally.\n\nEnglish: '{text}'")

    # Initialize the model with the exact name from the config file
    model = genai.GenerativeModel(model_name)

    response = model.generate_content(prompt)

    return response.text


# --- Main Execution Logic ---
if __name__ == "__main__":
    sample_text = "The food is very delicious! Where can I buy a motorcycle?"

    try:
        translated_text = translate_with_gemini(sample_text, TARGET_DIALECT.lower(), GEMINI_MODEL_NAME)

        print(f"\nOriginal:   {sample_text}")
        print(f"Translated: {translated_text}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

