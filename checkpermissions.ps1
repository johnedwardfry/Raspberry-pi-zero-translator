<#
.SYNOPSIS
    Checks if the currently authenticated gcloud user has the necessary IAM roles
    for the Cloud Translation and Vertex AI (Gemini) APIs in a specific project.
.DESCRIPTION
    This script is the PowerShell equivalent of the original bash script. It requires
    the Google Cloud SDK ('gcloud') to be installed and authenticated.
#>

# --- Google Cloud Permissions Checker ---
Clear-Host
Write-Host "--- Google Cloud Permissions Checker ---" -ForegroundColor Cyan
Write-Host ""

# 1. Get the currently active gcloud account
$ACCOUNT = gcloud config get-value account 2>$null

if ([string]::IsNullOrEmpty($ACCOUNT)) {
    Write-Host "❌ Error: No active gcloud account found." -ForegroundColor Red
    Write-Host "Please run 'gcloud auth login' and 'gcloud config set account <your-email>' first."
    exit 1
}

Write-Host "✅ Checking permissions for user: " -NoNewline; Write-Host $ACCOUNT -ForegroundColor Green
Write-Host ""

# 2. Get the Project ID from the user
$PROJECT_ID = Read-Host "Enter your Google Cloud Project ID"

if ([string]::IsNullOrEmpty($PROJECT_ID)) {
    Write-Host "❌ Error: Project ID cannot be empty." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Checking against project: " -NoNewline; Write-Host $PROJECT_ID -ForegroundColor Green
Write-Host ""
Write-Host "----------------------------------------"
Write-Host "Fetching IAM policy..."

# 3. Get the IAM policy and filter for the current user's assigned roles
try {
    $policyJson = gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --format="json" | ConvertFrom-Json
    $userRoles = $policyJson | Where-Object { $_.members -eq "user:$ACCOUNT" } | ForEach-Object { $_.bindings.role }
}
catch {
    Write-Host "❌ Error fetching IAM policy. Please check if the Project ID is correct and you have permission to view it." -ForegroundColor Red
    exit 1
}


if ($null -eq $userRoles) {
    Write-Host "⚠️  No specific roles found directly assigned to user: $ACCOUNT." -ForegroundColor Yellow
    Write-Host "   This is normal if you have inherited permissions (e.g., from a Google Group or as Project Owner)."
}

# --- Check for Cloud Translation Role ---
Write-Host ""
Write-Host "Checking for Cloud Translation role... " -NoNewline
if (($userRoles -join ' ') -match "roles/cloudtranslate.user|roles/editor|roles/owner") {
    Write-Host "[FOUND]" -ForegroundColor Green
    Write-Host "   You have one of the required roles: Cloud Translation API User, Editor, or Owner."
}
else {
    Write-Host "[MISSING]" -ForegroundColor Red
    Write-Host "   RECOMMENDATION: Grant the 'Cloud Translation API User' role to '$ACCOUNT' in the IAM console."
}
Write-Host ""

# --- Check for Vertex AI (Gemini) Role ---
Write-Host "Checking for Vertex AI (Gemini) role... " -NoNewline
if (($userRoles -join ' ') -match "roles/aiplatform.user|roles/editor|roles/owner") {
    Write-Host "[FOUND]" -ForegroundColor Green
    Write-Host "   You have one of the required roles: Vertex AI User, Editor, or Owner."
}
else {
    Write-Host "[MISSING]" -ForegroundColor Red
    Write-Host "   RECOMMENDATION: Grant the 'Vertex AI User' role to '$ACCOUNT' in the IAM console."
}
Write-Host ""

Write-Host "----------------------------------------"
Write-Host "Check complete." -ForegroundColor Cyan
