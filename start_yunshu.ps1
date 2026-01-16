# Yunshu System Startup Script

Write-Host "Starting Yunshu System..." -ForegroundColor Cyan

# 1. Kill port 8765
$port = 8765
$processId = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($processId) {
    Write-Host "Stopping old process (PID: $processId)..." -ForegroundColor Yellow
    Stop-Process -Id $processId -Force
    Start-Sleep -Seconds 1
    Write-Host "Old process stopped." -ForegroundColor Green
}

# 2. Set Env
# Ensure paths are absolute or correctly relative
$env:PYTHONPATH = "$PWD\components\mcp-feedback-enhanced;$PWD"
$env:MCP_WEB_PORT = "8765"
$env:MCP_WEB_HOST = "0.0.0.0"
$env:MCP_DEBUG = "true"

# 3. Start
Write-Host "Starting Core..." -ForegroundColor Cyan
Write-Host "Access URL: http://localhost:8765" -ForegroundColor Green

python -m mcp_feedback_enhanced