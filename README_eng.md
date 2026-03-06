<div align="center">

<img src="static/logo-small.png" width="100" height="100" alt="PhantomKey Logo">

# 👻 PhantomKey 🔑 (Out of Date)

### A simple and elegant open-source IoT access control bypass solution



*Available for Linux, Synology NAS, and Docker*

[![version](https://img.shields.io/badge/version-1.0.0-brightgreen.svg)](https://github.com/yourusername/phantomkey/releases)
[![LICENSE](https://img.shields.io/badge/license-MIT-yellowgreen.svg)](LICENSE)
[![build](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/yourusername/phantomkey/actions)
[![docker](https://img.shields.io/badge/docker-ready-cyan.svg)](https://hub.docker.com/r/yourusername/phantomkey)
[![platform](https://img.shields.io/badge/platform-Linux%20%7C%20NAS-lightgrey.svg)](https://github.com/yourusername/phantomkey)



[🎯 Motivation](#motivation) • [⚡ Features](#features) • [🏗️ Architecture](#architecture) • [📦 Deployment](#deployment) • [❓ FAQ](#faq)



*Built with ❤︎ by [Henry King](https://github.com/henrykingcn) and contributors*

</div>

---

## 🎯 Motivation

Traditional residential or smart home IoT access control apps often suffer from slow startup times and cumbersome steps. Every time you go home, you need to:

> 📱 Take out phone → 🔓 Unlock → 🔍 Find App → ⏳ Wait for splash screen/ads → 🏢 Find the corresponding building → 👆 Click to open

Furthermore, many IoT vendors' communication protocols involve **complex dynamic encryption** and **hardware fingerprinting**, making direct API reverse engineering costly and prone to failure.

### The Solution: PhantomKey 🎯

**PhantomKey** solves this problem through a **"dimensionality reduction"** approach:

1. Utilizes an **Android container** deployed on a local network server (NAS / Linux)
2. Runs the access control App **continuously in the background**
3. Uses **Python scripts** to achieve precise **UI automated clicks**
4. Provides a **minimalist Web dashboard** for true **"one-click instant unlock"**

---

## ⚡ Features

| Feature | Description |
|---------|-------------|
| 🚀 **Ultimate Speed** | Bypasses all splash screens and ads via Android container hot starts |
| 🔌 **Protocol Agnostic** | No need to reverse-engineer encrypted APIs; as long as the App can run, PhantomKey can control it |
| 🔄 **Hybrid Mode** | Supports "Silent Operation" and "Robust Mode" (Automatic reconnection and App reboot upon failure) |
| 🌐 **Cross-Platform Access** | Perfectly adapted for iOS Shortcuts, Safari home screen web apps, and Android desktop widgets |
| 👁️ **Visual Debugging** | Seamlessly supports `scrcpy` for real-time observation of the App's running state |

---

## 🏗️ Architecture

This solution adopts a **decoupled front-end and back-end design**. The core business logic runs in a closed loop within Docker containers.

### System Architecture Diagram

<img src="static/chart.png" width="700">


### Key Components

- **🐧 Host Server**: Your NAS or Ubuntu machine running Docker
- **🐳 Backend Container**: Flask API + Python UI automation script
- **🤖 Android Container**: Virtual Android environment with the access control app
- **☁️ Vendor Cloud**: IoT service provider's backend
- **🚪 Physical Door**: Smart lock or access control system

---

## 📦 Deployment

### ✅ Prerequisites

- A host machine supporting **Docker** (e.g., Ubuntu, Debian, or Synology NAS)
- A deployed **Android container** (recommending `redroid` or `budtmo/docker-android`)
  - ADB port `5555` must be mapped
- **PC Debugging Environment**: `adb` and `scrcpy` installed

### 📋 Step 1: Prepare Android Environment

Connect to your Android container from your PC using `scrcpy` (assuming container IP is `192.168.3.146`):

```bash
adb connect 192.168.3.146:5555
scrcpy -s 192.168.3.146:5555
```

**In the popup visual window:**
1. Install your access control App
2. Log in to your account
3. Navigate to the main interface containing the unlock button
4. Keep the app running in the background

### 🔧 Step 2: Deploy Core Backend API

It is **highly recommended** to use the provided `Dockerfile` to build the Python runtime environment to avoid polluting the host.

**Clone the repository and edit the global variables at the top of `server_sync.py`:**

```python
# Android container IP and ADB port
DEVICE_ADDR = "192.168.3.146:5555"
# Your access control App's package name
PACKAGE_NAME = 'com.yourvendor.iot'
```

**Build and run in the project root directory:**

```bash
# Build Docker image
docker build -t phantomkey-backend .

# Run container (mapping port 5010)
docker run -d --name pk-api -p 5010:5010 --restart unless-stopped phantomkey-backend
```

### 🌐 Step 3: Deploy Frontend Web Interface

Open the frontend file (`index.html`). Modify the `API_URL` variable to point to your newly deployed backend service address:

```javascript
const API_URL = "http://YOUR_SERVER_IP:5010/open_door";
```

**Deploy this HTML file to:**
- Any Web server (like Nginx, GitHub Pages)
- Or simply save it locally on your phone

💡 **Pro Tip:** Open the page in iOS Safari or Android Chrome and click **"Add to Home Screen"** in the share menu for an app-like experience.

---

## 🎨 Customization

If your access control App's UI differs from the default configuration, you need to use `weditor` or `uiautomatorviewer` to get the `resourceId` or `text` of the elements in your App, and modify the control logic in `server_sync.py`:

```python
# 1. Find and click the unlock Tab on the bottom menu bar
device(resourceId="your.app.package:id/target_id").click()

# 2. Find and click the specific unlock button (e.g., "Building 5" or "Unlock")
device(text="Unlock").click()

# 3. Set the success keyword for the verification Toast
if "Success" in message or "Unlocked" in message:
    return message
```

---

## ❓ FAQ

### Q: After clicking unlock on the frontend, it keeps spinning and finally shows "Connection Failed"?

> **A:** Please press **F12** (or use a packet capture tool on mobile) to inspect the network request.
> 
> Ensure:
> - `API_URL` is configured correctly
> - Port `5010` of the backend container is allowed through your firewall
> - Backend service is running: `docker ps`

### Q: The backend log shows `Unlock Tab not found (Timeout)`?

> **A:** This might be due to:
> - **Insufficient resource allocation** to the Android container causing extremely slow App startup
> - **App update** changing the UI element IDs
> 
> **Solution:** Use `scrcpy` to connect to the container and check the actual screen. Verify UI element IDs using `uiautomatorviewer`.

### Q: Why does it sometimes take 5-8 seconds to show success after clicking unlock?

> **A:** This is **normal**. It indicates that the system detected a **hot start failure** and triggered a **cold start** (**Robust Mode**).
> 
> The system is automatically:
> - Restarting the App in the background
> - Re-establishing the ADB connection
> - Ensuring the door is eventually unlocked successfully

### Q: Can I use this with multiple doors/buildings?

> **A:** Yes! You can:
> - Create multiple Flask API endpoints for different apps
> - Deploy multiple Android containers with different apps
> - Create a unified web dashboard with buttons for each location

### Q: Is this secure?

> **A:** Since PhantomKey operates on a **local network** with the Android container:
> - It does **NOT expose** the IoT vendor's API
> - It uses the official vendor app (you're not reverse-engineering)
> - Communication stays within your local network
> 
> **Best practice:** Use a VPN or other network security measures if accessing remotely.

---

## 📄 License

[MIT](../../LICENSE)

---

<div align="center">

### 🌟 If you found this helpful, please consider giving us a ⭐ on GitHub!

Made with ❤︎ for smart home enthusiasts

</div>
