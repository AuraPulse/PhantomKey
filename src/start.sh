#!/bin/bash

# 遇到错误立即停止
set -e

echo "========================================"
echo "   智能门禁后端环境自动部署脚本 (Docker版)"
echo "========================================"

# 1. 安装系统级依赖
echo "[1/5] 更新系统源并安装系统依赖 (ADB, Python3-venv)..."
apt-get update
# 注意：在 Ubuntu 容器里，python3-venv 通常是单独的包，必须安装
# android-tools-adb 是控制手机的关键
apt-get install -y python3 python3-pip python3-venv android-tools-adb

# 2. 创建虚拟环境
echo "[2/5] 检查/创建 Python 虚拟环境 (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo " -> 虚拟环境已创建在 ./venv"
else
    echo " -> 虚拟环境已存在，跳过创建"
fi

# 3. 激活环境并安装库
echo "[3/5] 激活虚拟环境并安装 Python 依赖..."
# 激活 venv
source venv/bin/activate

# 升级 pip (可选，但推荐)
pip install --upgrade pip

# 安装 Flask, uiautomator2 和 CORS
# flask-cors 是解决你前端无法连接问题的关键
echo " -> 正在安装 Flask, uiautomator2, flask-cors..."
pip install flask uiautomator2 flask-cors

# 4. ADB 预检
echo "[4/5] 启动 ADB 服务..."
adb start-server
adb devices

# 5. 启动服务
echo "[5/5] 准备启动服务..."

# 检查代码文件是否存在
if [ ! -f "app.py" ]; then
    echo "❌ 错误：在当前目录下找不到 'app.py'！"
    echo "请确保你把之前的 Python 代码保存为 'app.py' 并上传到这个目录。"
    exit 1
fi

echo "✅ 环境配置完毕！正在启动门禁后端..."
echo "端口: 5010"
echo "按 Ctrl+C 可以停止服务"
echo "----------------------------------------"

# 启动 Python 脚本
python app.py