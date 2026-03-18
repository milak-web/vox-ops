import base64
try:
    with open("qrcode.png", "rb") as f:
        print(base64.b64encode(f.read()).decode("utf-8"))
except Exception as e:
    print("ERROR:", e)