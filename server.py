from flask import Flask, send_from_directory, render_template_string
import socket
import os

app = Flask(__name__)

# Serve the main index.html file
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Serve static files (css, js)
@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('.', path)

def get_local_ips():
    ips = []
    try:
        # Get all network interfaces
        import psutil
        for interface, snics in psutil.net_if_addrs().items():
            for snic in snics:
                if snic.family == socket.AF_INET and not snic.address.startswith('127.'):
                    ips.append(snic.address)
    except Exception:
        # Fallback to simple method
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
            s.close()
        except Exception:
            ips.append("127.0.0.1")
    return list(set(ips))

if __name__ == '__main__':
    ips = get_local_ips()
    port = 5000
    
    print("\n" + "="*60)
    print(f"🚀 PixelForge Pro Server is running!")
    print(f"💻 Local Access: http://localhost:{port}")
    print("\n📱 Mobile Access (choose the one on your WiFi subnet):")
    for ip in ips:
        print(f"   👉 http://{ip}:{port}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
