$SERVER_IP = "43.156.149.105"
$SERVER_USER = "root"
$APP_DIR = "/opt/market-analysis"
$LOCAL_DIR = "c:\Users\alecl\Documents\Market_Analysis"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Uploading files to $SERVER_IP" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

ssh "${SERVER_USER}@${SERVER_IP}" "mkdir -p $APP_DIR"

$files = "app.py", "style.css", "requirements.txt", "processed_market_data.pkl", "market_analysis_24m.xlsx"

foreach ($file in $files) {
    $localPath = Join-Path $LOCAL_DIR $file
    if (Test-Path $localPath) {
        Write-Host "Uploading $file ..." -NoNewline
        scp $localPath "${SERVER_USER}@${SERVER_IP}:${APP_DIR}/"
        Write-Host " Done" -ForegroundColor Green
    } else {
        Write-Host "Skipping (not found): $file" -ForegroundColor Yellow
    }
}

Write-Host "Uploading deploy.sh ..." -NoNewline
scp "$LOCAL_DIR\deploy\deploy.sh" "${SERVER_USER}@${SERVER_IP}:/tmp/deploy.sh"
ssh "${SERVER_USER}@${SERVER_IP}" "chmod +x /tmp/deploy.sh"
Write-Host " Done" -ForegroundColor Green

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host " Upload complete!" -ForegroundColor Green
Write-Host " Next: ssh root@$SERVER_IP" -ForegroundColor Cyan
Write-Host "        bash /tmp/deploy.sh" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Green
