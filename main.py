import configparser
import google.generativeai as genai
from google.cloud import translate_v2
from google.cloud import translate as translate_v3

# --- Configuration Loader ---
config = configparser.ConfigParser()
config.read('config.ini')

# Standard Translation API settings
USE_ADVANCED_API = config['settings'].getboolean('use_advanced_api')
GCP_PROJECT_ID = config['settings']['gcp_project_id']

# Gemini API settings
TRANSLATION_MODEL = config['gemini_settings']['translation_model']
TARGET_DIALECT = config['gemini_settings']['target_dialect']

# Configure the Gemini client (remember to set your API key as an environment variable)
# In PyCharm: Run > Edit Configurations > Environment variables
genai.configure(api_key="YOUR_GOOGLE_API_KEY")


# --- Translation Functions ---

def translate_with_gemini_dialects(text, dialect):
    """Translates text using Gemini with dialect-specific instructions."""
    print(f"--- Using Gemini API for '{dialect}' dialect ---")

    # Create the prompt based on the dialect setting
    prompt = f"Translate the following English text into Thai: '{text}'"

    if dialect == "northern":
        prompt = (f"Translate the following English text into Thai, using a friendly, informal tone "
                  f"appropriate for the Northern Thai (Lanna) dialect. Emphasize clarity but "
                  f"incorporate common Northern vocabulary if natural.\n\nEnglish: '{text}'")
    elif dialect == "southern":
        prompt = (f"Translate the following English text into Thai, using a direct and clear tone "
                  f"appropriate for the Southern Thai (Pak Tai) dialect. Use common Southern "
                  f"phrasing where it fits naturally.\n\nEnglish: '{text}'")

    # Initialize the model and get the translation
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    response = model.generate_content(prompt)

    return response.text


def translate_basic(text, target_language="th"):
    """Translates text using the Basic v2 API."""
    print("--- Using Basic (v2) Google Translate API ---")
    client = translate_v2.Client()
    result = client.translate(text, target_language=target_language)
    return result['translatedText']


def translate_advanced(text, target_language="th"):
    """Translates text using the Advanced v3 API."""
    print("--- Using Advanced (v3) Google Translate API ---")
    client = translate_v3.TranslationServiceClient()
    parent = f"projects/{GCP_PROJECT_ID}/locations/global"
    response = client.translate_text(
        request={"parent": parent, "contents": [text], "mime_type": "text/plain",
                 "target_language_code": target_language}
    )
    return response.translations[0].translated_text


# --- Main Execution Logic ---
if __name__ == "__main__":
    sample_text = "The food is very delicious! Where can I buy a motorcycle?"
    translated_text = ""

    try:
        if TRANSLATION_MODEL.lower() == 'gemini':
            translated_text = translate_with_gemini_dialects(sample_text, TARGET_DIALECT.lower())
        else:
            if USE_ADVANCED_API:
                translated_text = translate_advanced(sample_text)
            else:
                translated_text = translate_basic(sample_text)

        print(f"\nOriginal: {sample_text}")
        print(f"Translated: {translated_text}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")