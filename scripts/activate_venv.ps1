# GeoMind 虚拟环境激活脚本 (PowerShell)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$VenvPath = Join-Path $ProjectRoot "venv"

if (-not (Test-Path $VenvPath)) {
    Write-Host "虚拟环境不存在，正在创建..." -ForegroundColor Yellow
    
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "错误: 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
        exit 1
    }
    
    python -m venv $VenvPath
    Write-Host "虚拟环境创建成功！" -ForegroundColor Green
}

Write-Host "激活虚拟环境: $VenvPath" -ForegroundColor Cyan
& "$VenvPath\Scripts\Activate.ps1"

Write-Host "虚拟环境已激活！" -ForegroundColor Green
Write-Host "提示: 使用 'deactivate' 退出虚拟环境" -ForegroundColor Yellow

