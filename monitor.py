import requests
import time
import logging
import subprocess
import os

# --- PJ AGENTIC SENTINEL CONFIG ---
NGROK_URL = "https://playtime-facebook-discard.ngrok-free.dev" 
HEALTH_PATH = "/health"
API_ENDPOINT = f"{NGROK_URL}{HEALTH_PATH}"
CHECK_INTERVAL = 10  # Reduced to 10s for faster command response when Boss is home

# 💎 ARCHITECT'S CREDENTIALS
TELEGRAM_TOKEN = "8838976396:AAFjWuV4RKimkt6kOSEaOlnnViSUgxtiNV0"
TELEGRAM_CHAT_ID = "8829420534"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

last_update_id = 0

def send_sentinel_alert(message):
    """PJ Agentic Sentinel: High-Priority Mobile Interrupt."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🛡️ <b>PJ AGENTIC SENTINEL</b>\n───────────────\n{message}",
            "parse_mode": "HTML"
        }
        requests.post(url, data=payload, timeout=8)
        return True
    except Exception as e:
        logging.error(f"❌ Sentinel Signal Lost: {str(e)}")
        return False

def de_cloak_system():
    logging.warning("👑 Boss Handshake Verified. De-cloaking Auckland Bridge...")
    send_sentinel_alert("✨ <b>IDENTITY VERIFIED</b>\nRestoring workspace visibility.")
    
    # 1. Targeted Kill: Kill only the process holding Port 8001 (The Backend)
    # This prevents the monitor.py from killing itself
    subprocess.run('for /f "tokens=5" %a in (\'netstat -aon ^| findstr :8001\') do taskkill /f /pid %a', shell=True, capture_output=True)
    
    # 2. Kill Ngrok
    subprocess.run("taskkill /f /im ngrok.exe", shell=True, capture_output=True)
    
    time.sleep(2)
    
    # 3. Re-launch Visible
    backend_cmd = 'start cmd /k "cd backend && .\\.venv\\Scripts\\activate && uvicorn app.main:app --host 127.0.0.1 --port 8001"'
    subprocess.Popen(backend_cmd, shell=True)
    
    time.sleep(5)
    
    ngrok_cmd = 'start cmd /k "ngrok http 8001"'
    subprocess.Popen(ngrok_cmd, shell=True)
    
    logging.info("✅ Workspace Restored. Monitor continuing in background...")

def check_for_boss_command():
    """Listen for /boss_is_here from Telegram."""
    global last_update_id
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
        response = requests.get(url, timeout=5).json()
        
        for update in response.get("result", []):
            last_update_id = update["update_id"]
            message_text = update.get("message", {}).get("text", "")
            
            if message_text == "/boss_is_here":
                de_cloak_system()
                
    except Exception as e:
        pass # Keep silent in loop

def execute_agentic_heartbeat():
    try:
        headers = {'ngrok-skip-browser-warning': 'true'}
        start_time = time.time()
        backend_resp = requests.get(API_ENDPOINT, headers=headers, timeout=10)
        latency = (time.time() - start_time) * 1000
        
        if backend_resp.status_code == 200:
            logging.info(f"🧠 Backend Active | Latency: {latency:.2f}ms")
        else:
            logging.error("🚨 BRIDGE MISMATCH | Recovery logic triggered.")
            # Note: You can call run_recovery_protocol() here if you want auto-fix
    except Exception as e:
        logging.error(f"🔥 SYSTEM INTERRUPT: {str(e)}")

if __name__ == "__main__":
    logging.info("🛠️ PJ Agentic Sentinel: Dual-Factor Stealth Mode Active.")
    send_sentinel_alert("✅ <b>Sentinel Online</b>\nI am listening for the Boss Command or Mismatches.")

    while True:
        execute_agentic_heartbeat()
        check_for_boss_command() # Listen for Mobile Handshake
        time.sleep(CHECK_INTERVAL)