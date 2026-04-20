import requests
import time
import logging

# --- PJ AGENTIC SENTINEL CONFIG ---
NGROK_URL = "https://playtime-facebook-discard.ngrok-free.dev" 
HEALTH_PATH = "/health"
API_ENDPOINT = f"{NGROK_URL}{HEALTH_PATH}"
CHECK_INTERVAL = 300 

# 💎 ARCHITECT'S CREDENTIALS
TELEGRAM_TOKEN = "8629765611:AAEt_3Hz8TLRxEIiuJ10VILagSv0ZC0lDDA"
TELEGRAM_CHAT_ID = "6374596694"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

def send_sentinel_alert(message):
    """PJ Agentic Sentinel: High-Priority Mobile Interrupt."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🛡️ <b>PJ AGENTIC SENTINEL</b>\n───────────────\n{message}",
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=payload, timeout=8)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"❌ Sentinel Signal Lost: {str(e)}")
        return False

def execute_agentic_heartbeat():
    try:
        headers = {'ngrok-skip-browser-warning': 'true'}
        start_time = time.time()
        
        backend_resp = requests.get(API_ENDPOINT, headers=headers, timeout=15)
        latency = (time.time() - start_time) * 1000
        
        if backend_resp.status_code == 200:
            data = backend_resp.json()
            logging.info(f"🧠 Agentic Backend Active | Signal: {data.get('status')} | Latency: {latency:.2f}ms")
            
            # ALERT: High Latency Threshold (3 seconds)
            if latency > 3000:
                send_sentinel_alert(f"⚠️ <b>High Latency Spike</b>\nStatus: Active\nLatency: {latency:.2f}ms\n<i>Action: Check Auckland network load.</i>")
        
        else:
            # ALERT: Bridge Mismatch (Critical)
            error_msg = f"🚨 <b>BRIDGE MISMATCH</b>\nStatus: {backend_resp.status_code}\nPath: {HEALTH_PATH}\n<i>Action: Restart Ngrok Tunnel immediately.</i>"
            logging.error(error_msg)
            send_sentinel_alert(error_msg)

    except Exception as e:
        # ALERT: System Crash
        interrupt_msg = f"🔥 <b>SYSTEM INTERRUPT</b>\nLog: {str(e)[:100]}...\n<i>Action: Check local server status.</i>"
        logging.error(interrupt_msg)
        send_sentinel_alert(interrupt_msg)

if __name__ == "__main__":
    logging.info("🛠️ Initializing PJ Agentic Sentinel...")
    
    # Startup Handshake
    success = send_sentinel_alert("✅ <b>Sentinel Monitoring: ONLINE</b>\nAuckland Bridge is now under PJ signature protection.")
    
    if success:
        logging.info("📡 Sentinel Handshake Successful. Mobile alerts active.")
    else:
        logging.warning("⚠️ Sentinel Handshake Failed. Check Chat ID.")

    while True:
        execute_agentic_heartbeat()
        time.sleep(CHECK_INTERVAL)