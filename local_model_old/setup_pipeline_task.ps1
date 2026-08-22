# Sinhala Call Analytics — Pipeline Scheduled Task Setup
# Run this script (as Administrator) to install the pipeline watcher as a startup task.

$TaskName = "SinhalaCallAnalytics-Pipeline"
$ProjectDir = "C:\Users\udaya\OneDrive\Desktop\sinhala_call_analytics"

# Use the virtual environment Python (has torch + all deps installed)
# Use VBS launcher to run python.exe without a console window
$VbsLauncher = "$ProjectDir\run_pipeline_hidden.vbs"

if (-not (Test-Path $Python)) {
    Write-Error "Virtual environment Python not found at: $Python"
    Write-Error "Run 'uv venv' or 'python -m venv .venv' first."
    exit 1
}

Write-Host "Project: $ProjectDir"
Write-Host "Launcher: $VbsLauncher"
Write-Host ""

# Create the task (VBS launcher runs Python silently in background)
$Action = New-ScheduledTaskAction `
    -Execute "$VbsLauncher" `
    -WorkingDirectory "$ProjectDir"

# Run at user logon
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# Restart if it crashes (3 attempts, 1 minute apart)
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Processes .txt transcript files from incoming folder using ML pipeline" `
    -Force

if ($?) {
    Write-Host ""
    Write-Host "Task '$TaskName' created successfully!" -ForegroundColor Green
    Write-Host "It will run automatically at your next logon." -ForegroundColor Green
    Write-Host ""
    Write-Host "To start it immediately without logging off:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To stop it:" -ForegroundColor Yellow
    Write-Host "  Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To remove it:" -ForegroundColor Yellow
    Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Cyan
}
