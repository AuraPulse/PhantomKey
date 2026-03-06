from flask import Flask, jsonify
from flask_cors import CORS  # 必须安装: pip install flask-cors
import uiautomator2 as u2
import threading
import subprocess
import time

app = Flask(__name__)
# 允许所有跨域请求
CORS(app) 

# --- Global Configuration ---
DEVICE_ADDR = "192.168.3.146:5555" # 修改成ADB设备
PACKAGE_NAME = 'com.taichuan.iot' # 修改成APP包名

# --- Global Variables ---
task_lock = threading.Lock()
d = None 

# --- Helper Functions ---
def run_shell(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except Exception as e:
        print(f"[System] Command error: {e}")
        return ""

def force_reconnect_adb():
    print(f"[ADB] Forcing reconnect to {DEVICE_ADDR}...")
    run_shell(f"adb disconnect {DEVICE_ADDR}")
    time.sleep(1)
    run_shell(f"adb connect {DEVICE_ADDR}")
    time.sleep(2) # 等待 ADB 握手
    return True

def get_device():
    global d
    if d:
        try:
            if d.info: return d
        except:
            d = None
    
    print("[u2] Connecting...")
    if f"{DEVICE_ADDR}\tdevice" not in run_shell("adb devices"):
        force_reconnect_adb()
    
    try:
        d = u2.connect(DEVICE_ADDR)
        return d
    except Exception as e:
        print(f"[u2] Connect fail: {e}")
        return None

# --- Core Logic (Updated with Smart Retry Strategy) ---
def attempt_unlock(force_stop=False):
    """
    尝试开门
    :param force_stop: False=热启动(快), True=冷启动(稳,杀进程)
    """
    device = get_device()
    if not device:
        raise Exception("Cannot connect to Android Emulator")

    # 1. 唤醒屏幕 (防止锁屏点击无效)
    try:
        if not device.info.get('screenOn'):
            device.screen_on()
            device.swipe(0.5, 0.9, 0.5, 0.1)
    except:
        pass 

    # 2. 启动 App (策略调整核心)
    print(f"[Step] Starting App (ForceStop={force_stop})...")
    device.app_start(PACKAGE_NAME, stop=force_stop)
    
    # 3. 等待 App 界面
    # 如果是热启动(App原本就开着)，界面应该秒出，所以只等3秒，没出就报错重试
    # 如果是冷启动，需要等启动画面，给10秒
    wait_timeout = 10 if force_stop else 3
    
    if not device(resourceId="com.taichuan.iot:id/app_tab_unlock_button").wait(timeout=wait_timeout):
        raise Exception(f"Unlock Tab not found within {wait_timeout}s (App stuck?)")

    # 4. 点击解锁 Tab
    device(resourceId="com.taichuan.iot:id/app_tab_unlock_button").click()
    # 热启动时不需要sleep太久
    time.sleep(0.5)

    # 5. 点击开门按钮 & 验证 Toast
    if device(text="5栋").exists(timeout=3):
        
        # [关键步骤 A] 重置 Toast 缓存
        device.toast.reset()
        
        # [关键步骤 B] 点击按钮
        print("[Step] Clicking '5栋' button...")
        device(text="5栋").click()
        
        # [关键步骤 C] 捕获 Toast 消息
        print("[Step] Waiting for success message (Toast)...")
        message = device.toast.get_message(wait_timeout=5.0, default=None)
        
        if message:
            print(f"[System] Detected Toast: {message}")
            if "成功" in message or "开锁" in message or "Success" in message:
                return message
            else:
                raise Exception(f"Operation Failed. System said: {message}")
        else:
            raise Exception("Button clicked but NO success message detected.")
            
    else:
        raise Exception("Button '5栋' not found on screen")

# --- API Route ---
@app.route('/open_door', methods=['GET'])
def open_door_api():
    if task_lock.locked():
        return jsonify({"status": "error", "message": "System is busy processing..."}), 429

    with task_lock:
        print("\n--- New Request Received ---")
        try:
            # === 第一次尝试：极速模式 ===
            # 不强制重启，尝试直接操作
            print(">>> Attempt 1: Fast Mode (Hot Start) <<<")
            msg = attempt_unlock(force_stop=False)
            print(f"--- Success: {msg} ---")
            return jsonify({"status": "success", "message": f"Door Opened: {msg}"})
        
        except Exception as e1:
            # === 失败处理 ===
            print(f"[Warn] Fast Mode failed: {e1}")
            print(">>> Attempt 2: Robust Mode (Cold Start & Reconnect) <<<")
            
            try:
                # 销毁旧对象，重连ADB
                global d
                d = None
                force_reconnect_adb()
                
                # === 第二次尝试：稳定模式 ===
                # 强制重启 App (stop=True)，修复一切卡死
                msg = attempt_unlock(force_stop=True) 
                print(f"--- Retry Success: {msg} ---")
                return jsonify({"status": "success", "message": f"Door Opened (Retry): {msg}"})
            
            except Exception as e2:
                print(f"[Error] Final failure: {e2}")
                return jsonify({"status": "error", "message": str(e2)}), 500

if __name__ == '__main__':
    print(">>> Starting Door Server v2.1 (Smart Retry Strategy) <<<")
    force_reconnect_adb()
    app.run(host='0.0.0.0', port=5010)