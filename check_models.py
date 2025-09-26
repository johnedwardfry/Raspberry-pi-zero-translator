import configparser
import vertexai
from vertexai.generative_models import GenerativeModel

# --- Configuration Loader ---
try:
    config = configparser.ConfigParser()
    config.read('config.ini')
    GCP_PROJECT_ID = config['settings']['gcp_project_id']
    GCP_REGION = config['settings']['gcp_region']
except Exception as e:
    print(f"Error: Could not read 'gcp_project_id' or 'gcp_region' from config.ini.")
    print(f"Underlying error: {e}")
    exit()

# --- Initialize Vertex AI ---
try:
    print(f"Initializing Vertex AI for project '{GCP_PROJECT_ID}' in region '{GCP_REGION}'...")
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    print("Initialization successful.")
except Exception as e:
    print(f"Error initializing Vertex AI: {e}")
    exit()

# --- List Available Models ---
try:
    print("\n--- Fetching available generative models... ---")
    models = GenerativeModel.list_models()

    if not models:
        print("No models found for your project in this region.")
    else:
        print(f"Found {len(models)} models:")
        for model in models:
            # We are primarily interested in the Gemini models
            if 'gemini' in model.name:
                print(f"- {model.name}")

    print("-------------------------------------------\n")
    print("Check complete. Please use one of the model names listed above in your config.ini file.")

except Exception as e:
    print(f"\nAn error occurred while fetching models: {e}")
