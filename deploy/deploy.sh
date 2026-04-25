#!/bin/bash
# ============================================================
#  Amazon Market Analysis - 一键部署脚本 (服务器端)
#  适用: 腾讯云/阿里云 Ubuntu 20.04+ / CentOS 7+
#  用法: bash deploy.sh
# ============================================================

set -e  # 出错立即退出

APP_DIR="/opt/market-analysis"
SERVICE_NAME="market-analysis"
PORT=8501

echo "=============================================="
echo " 🚀 Amazon Market Analysis 一键部署脚本"
echo "=============================================="

# --- 1. 检测系统 ---
echo "[1/6] 检测系统环境..."
if command -v apt-get &>/dev/null; then
    PKG_MANAGER="apt-get"
    echo "  ✅ 检测到 Ubuntu/Debian 系统"
elif command -v yum &>/dev/null; then
    PKG_MANAGER="yum"
    echo "  ✅ 检测到 CentOS/RHEL 系统"
else
    echo "  ❌ 不支持的系统，请使用 Ubuntu 或 CentOS"
    exit 1
fi

# --- 2. 安装 Python3 & pip ---
echo "[2/6] 安装 Python3 和 pip..."
if [ "$PKG_MANAGER" = "apt-get" ]; then
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv -qq
else
    yum install -y python3 python3-pip -q
fi
echo "  ✅ Python 版本: $(python3 --version)"

# --- 3. 创建应用目录 ---
echo "[3/6] 创建应用目录: $APP_DIR"
mkdir -p $APP_DIR
echo "  ✅ 目录已创建"

# --- 4. 安装 Python 依赖 (虚拟环境) ---
echo "[4/6] 创建虚拟环境并安装依赖..."
python3 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate

# 使用国内镜像加速 pip 安装
pip install --upgrade pip -q -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install streamlit pandas plotly openpyxl -q -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo "  ✅ 依赖安装完成"
deactivate

# --- 5. 创建 Streamlit 配置 ---
echo "[5/6] 配置 Streamlit..."
mkdir -p $APP_DIR/.streamlit
cat > $APP_DIR/.streamlit/config.toml << EOF
[server]
port = $PORT
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false
maxUploadSize = 200

[theme]
base = "light"
primaryColor = "#2563eb"
backgroundColor = "#f8fafc"
secondaryBackgroundColor = "#ffffff"
textColor = "#1e293b"

[browser]
serverAddress = "0.0.0.0"
gatherUsageStats = false
EOF
echo "  ✅ Streamlit 配置已写入"

# --- 6. 创建 systemd 服务 (开机自启, 后台运行) ---
echo "[6/6] 创建系统服务 (开机自启)..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Amazon Market Analysis Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/streamlit run $APP_DIR/app.py --server.port=$PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

echo ""
echo "=============================================="
echo " ✅ 部署完成！"
echo "=============================================="
echo ""

# 获取服务器 IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo " 🌐 访问地址: http://$SERVER_IP:$PORT"
echo " 📋 管理命令:"
echo "   查看状态: systemctl status $SERVICE_NAME"
echo "   重启应用: systemctl restart $SERVICE_NAME"
echo "   查看日志: journalctl -u $SERVICE_NAME -f"
echo ""
echo " ⚠️  请确保云服务器安全组已开放 TCP 端口 $PORT"
echo "=============================================="
