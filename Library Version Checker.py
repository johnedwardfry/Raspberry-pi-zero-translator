import google.cloud.aiplatform

try:
    print("\n--- Checking installed library version ---")
    version = google.cloud.aiplatform.__version__
    print(f"Version of 'google-cloud-aiplatform' is: {version}")

    # Generally, versions 1.38.0 and newer are required for the latest features.
    major, minor, _ = map(int, version.split('.'))
    if major >= 1 and minor >= 38:
        print("This version is recent and should work correctly.")
    else:
        print("WARNING: This version is old. Please run 'pip install --upgrade google-cloud-aiplatform'.")

    print("----------------------------------------\n")

except Exception as e:
    print(f"An error occurred: {e}")
