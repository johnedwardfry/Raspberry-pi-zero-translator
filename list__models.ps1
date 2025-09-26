<#
.SYNOPSIS
    Lists the generative AI models available in a specific GCP project and region.
.DESCRIPTION
    This script uses the gcloud command-line tool to query the Vertex AI platform
    and return a list of all available publisher models. This is useful for
    diagnosing 404 Not Found errors.
#>

Clear-Host
Write-Host "--- Vertex AI Model Lister (Broad Scan) ---" -ForegroundColor Cyan
Write-Host ""

# 1. Get the Project ID from the user
$PROJECT_ID = Read-Host "Enter your Google Cloud Project ID (e.g., translator-pi-v2)"

if ([string]::IsNullOrEmpty($PROJECT_ID)) {
    Write-Host "❌ Error: Project ID cannot be empty." -ForegroundColor Red
    exit 1
}

# 2. Get the Region from the user
$REGION = Read-Host "Enter the GCP Region from your config.ini (e.g., us-central1)"

if ([string]::IsNullOrEmpty($REGION)) {
    Write-Host "❌ Error: Region cannot be empty." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Querying for ALL available models in project '$PROJECT_ID' and region '$REGION'..."
Write-Host "This may take a moment."
Write-Host "------------------------------------------------------------------"

# 3. Run the gcloud command to list models and format the output
try {
    # This command now lists ALL models without filtering.
    gcloud ai models list --region=$REGION --project=$PROJECT_ID --format="value(MODEL_ID)"
}
catch {
    Write-Host "❌ An error occurred while running the gcloud command." -ForegroundColor Red
    Write-Host "   Please ensure you are logged in ('gcloud auth login') and the project/region are correct."
}

Write-Host "------------------------------------------------------------------"
Write-Host "Query complete." -ForegroundColor Green

