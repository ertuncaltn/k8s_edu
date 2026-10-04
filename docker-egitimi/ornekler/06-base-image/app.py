import socket
from flask import Flask

app = Flask(__name__)

# Bu satırı değiştirip yeniden build ederek cache davranışını gözlemleyin
MESAJ = "Merhaba Docker!"


@app.route("/")
def index():
    return f"{MESAJ} (container: {socket.gethostname()})\n"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
