# Quick check: Ollama reachable + model listed. No heavy generate.
param(
  [string]$OllamaHost = "http://localhost:11434"
)

$ErrorActionPreference = "Stop"
Write-Host "Checking Ollama at $OllamaHost ..." -ForegroundColor Cyan

try {
  $v = Invoke-RestMethod -Uri "$OllamaHost/api/version" -TimeoutSec 5
  Write-Host "Ollama version: $($v.version)" -ForegroundColor Green
} catch {
  Write-Host "Cannot reach Ollama. Is it running? (e.g. start Ollama app or 'ollama serve')" -ForegroundColor Red
  exit 1
}

try {
  $tags = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -TimeoutSec 5
  $names = $tags.models | ForEach-Object { $_.name }
  Write-Host "Models: $($names -join ', ')" -ForegroundColor Green
  $hasQwen = ($names | Where-Object { $_ -match "qwen3\.5" }).Count -gt 0
  if (-not $hasQwen) {
    Write-Host "Tip: Run 'ollama pull qwen3.5:latest' if you want to use default model." -ForegroundColor Yellow
  }
} catch {
  Write-Host "Could not list models: $_" -ForegroundColor Yellow
}

Write-Host "`nConnection OK. Run: .\run.ps1 -Topic '你的主题' -Goal 私信咨询" -ForegroundColor Cyan
