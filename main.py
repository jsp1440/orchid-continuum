from app import app

# CRITICAL: Start real-time integrity monitoring on server startup
try:
    from realtime_integrity_guardian import start_integrity_monitoring
    start_integrity_monitoring()
    print("🛡️ INTEGRITY GUARDIAN ACTIVATED - Zero tolerance monitoring started")
except Exception as e:
    print(f"🚨 CRITICAL: Failed to start integrity guardian: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
