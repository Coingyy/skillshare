# One-time setup: deploys the submission worker and sets its secrets.
# Run:  powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "[1/3] Deploying worker to Cloudflare..." -ForegroundColor Green
npx --yes wrangler deploy

Write-Host ""
Write-Host "[2/3] Setting crew code (vibecrew-2026)..." -ForegroundColor Green
"vibecrew-2026" | npx --yes wrangler secret put FRIEND_CODE

Write-Host ""
Write-Host "[3/3] GitHub token" -ForegroundColor Green
Write-Host "Create it here if you haven't: https://github.com/settings/personal-access-tokens/new"
Write-Host "(Only select repositories: Coingyy/skillshare -> Permissions -> Issues: Read and write)"
$token = Read-Host "Paste the GitHub token and press Enter"
$token.Trim() | npx --yes wrangler secret put GH_TOKEN

Write-Host ""
Write-Host "Done! Tell Claude 'setup fertig' to finish up." -ForegroundColor Green
