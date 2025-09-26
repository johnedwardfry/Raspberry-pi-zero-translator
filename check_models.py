import google.generativeai as genai

# --- IMPORTANT ---
# Copy your API key from your config.ini file and paste it here between the quotes.
API_KEY = "PASTE_YOUR_GOOGLE_API_KEY_HERE"

# Configure the library with your key
genai.configure(api_key=API_KEY)

print("--- Fetching Available Gemini Models ---")

# The list_models() function returns an iterable object
for m in genai.list_models():
  # Check if the model supports the 'generateContent' method
  if 'generateContent' in m.supported_generation_methods:
    print(f"Model Name: {m.name}")

print("\n--- End of List ---")