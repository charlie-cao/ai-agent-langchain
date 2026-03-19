param(
  [Parameter(Mandatory=$false)][string]$Model = "qwen3.5:latest",
  [Parameter(Mandatory=$false)][string]$Platform = "小红书",
  [Parameter(Mandatory=$true)][string]$Topic,
  [Parameter(Mandatory=$false)][string]$Audience = "",
  [Parameter(Mandatory=$false)][string]$Goal = "收藏",
  [Parameter(Mandatory=$false)][string]$Offer = "",
  [Parameter(Mandatory=$false)][string]$Proof = "暂无",
  [Parameter(Mandatory=$false)][string]$Tone = "专业+克制",
  [Parameter(Mandatory=$false)][string]$Constraints = "",
  [Parameter(Mandatory=$false)][string]$Format = "图文",
  [Parameter(Mandatory=$false)][string]$Deliverables = "",
  [Parameter(Mandatory=$false)][int]$TimeoutSec = 180,
  [Parameter(Mandatory=$false)][string]$OllamaHost = "http://localhost:11434"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$systemPath = Join-Path $root "prompts\system.txt"

if (!(Test-Path $systemPath)) {
  throw "Missing prompts/system.txt at $systemPath"
}

$system = Get-Content -Raw -Encoding UTF8 $systemPath

$user = @"
请按“固定输出格式”生成，不要解释过程，不要省略任何区块。

Platform：$Platform
Topic：$Topic
Audience：$Audience
Goal：$Goal
Offer：$Offer
Proof：$Proof
Tone：$Tone
Constraints：$Constraints
Format：$Format
Deliverables：$Deliverables
"@

# Use Ollama HTTP API for one-shot run (no interactive wait)
$body = @{
  model  = $Model
  prompt  = $user
  system  = $system
  stream  = $false
  options = @{ temperature = 0.6; num_predict = 4096 }
} | ConvertTo-Json -Depth 4 -Compress

$uri = "$OllamaHost/api/generate"
Write-Host "Calling Ollama API: $Model (timeout ${TimeoutSec}s)..." -ForegroundColor Cyan

try {
  $response = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/json; charset=utf-8" -TimeoutSec $TimeoutSec
  if ($response.error) {
    Write-Host "Ollama API error: $($response.error)" -ForegroundColor Red
    exit 1
  }
  if ($response.response) {
    Write-Host "`n--- Output ---`n" -ForegroundColor Green
    $response.response
  } else {
    Write-Host "No response text in API result." -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 3
  }
} catch {
  Write-Host "API Error: $_" -ForegroundColor Red
  Write-Host "Tip: Ensure 'ollama serve' is running (ollama usually runs in background)." -ForegroundColor Yellow
  exit 1
}
