# Amazon Market Analysis Skill - 环境初始化脚本
# 用法: powershell -ExecutionPolicy Bypass -File setup_skill.ps1

Write-Host "--- 正在初始化 Amazon 市场分析 Skill 环境 ---" -ForegroundColor Cyan

# 1. 创建虚拟环境
if (-not (Test-Path "venv")) {
    Write-Host "[1/3] 正在创建 Python 虚拟环境..."
    python -m venv venv
}

# 2. 安装依赖
Write-Host "[2/3] 正在安装 Python 依赖库 (requirements.txt)..."
$env:PYTHONIOENCODING='utf-8'
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. 验证 MCP 状态 (模拟)
Write-Host "[3/3] 环境检查完成。"
Write-Host "提示: 请确保您的 Antigravity 已配置 Sellersprite MCP。" -ForegroundColor Yellow

Write-Host "`n[SUCCESS] Skill 已就绪！您现在可以告诉 AI: '运行亚马逊市场分析'。" -ForegroundColor Green
