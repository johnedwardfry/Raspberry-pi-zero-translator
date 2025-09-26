import configparser
from google.cloud import aiplatform

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
    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    print("Initialization successful.")
except Exception as e:
    print(f"Error initializing Vertex AI: {e}")
    exit()

# --- List Available Models ---
try:
    print("\n--- Fetching available generative models... ---")
    # This is a more robust, lower-level method to list all models in the project.
    models = aiplatform.Model.list()

    if not models:
        print("No models found for your project in this region.")
    else:
        print(f"Found {len(models)} models. Filtering for Gemini models:")
        gemini_models_found = False
        for model in models:
            # We are primarily interested in the Gemini models.
            # The model object has a 'display_name' attribute.
            if 'gemini' in model.display_name:
                # The name we need for the SDK is in the 'resource_name'
                # but we'll display the friendly name.
                print(f"- Display Name: {model.display_name}")
                # The resource_name often contains the versioned name we can use.
                print(f"  Resource Name: {model.resource_name}\n")
                gemini_models_found = True

        if not gemini_models_found:
            print("\nNOTE: No models with 'gemini' in the name were found.")

    print("-------------------------------------------\n")
    print("Check complete.")

except Exception as e:
    print(f"\nAn error occurred while fetching models: {e}")


