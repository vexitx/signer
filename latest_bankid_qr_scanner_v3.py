import tkinter as tk, numpy as np, cv2, time, socketio, mss, importlib.util, hmac, hashlib
from tkinter import ttk
from threading import Thread

pyzbar_available = importlib.util.find_spec("pyzbar") is not None
if not pyzbar_available:
    print("Note: For better QR code detection, install pyzbar: pip install pyzbar")
else:
    from pyzbar.pyzbar import decode as pyzbar_decode

sio = socketio.Client()
stop_scanning = False
scanned_data = {}

class ModernButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Enter>", lambda e: self.config(background="#7C3AED"))
        self.bind("<Leave>", lambda e: self.config(background="#8B5CF6"))

def enhance_qr_image(frame):
    enhanced_images = []
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) if len(frame.shape) > 2 else frame
    enhanced_images.append(gray)
    
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    enhanced_images.append(thresh)
    
    kernel = np.ones((3, 3), np.uint8)
    morph = cv2.morphologyEx(cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel), cv2.MORPH_OPEN, kernel)
    enhanced_images.append(morph)
    
    if len(frame.shape) > 2:
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        lower_red1, upper_red1 = np.array([0, 70, 50]), np.array([10, 255, 255])
        lower_red2, upper_red2 = np.array([170, 70, 50]), np.array([180, 255, 255])
        red_mask = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1), cv2.inRange(hsv, lower_red2, upper_red2))
        red_enhanced = cv2.bitwise_not(red_mask)
        enhanced_images.extend([
            red_enhanced,
            cv2.morphologyEx(cv2.morphologyEx(red_enhanced, cv2.MORPH_CLOSE, kernel), cv2.MORPH_OPEN, kernel),
            cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray),
            cv2.bitwise_not(gray),
            cv2.dilate(cv2.Canny(gray, 100, 200), kernel, iterations=1)
        ])
    return enhanced_images

def scan_for_qr_codes(frame):
    results = []
    detected = False
    detected_data = None
    detector = cv2.QRCodeDetector()
    
    def try_detection(img, method_prefix=""):
        nonlocal detected, detected_data
        data, points, _ = detector.detectAndDecode(img)
        if data:
            method_name = f"{method_prefix}opencv"
            results.append({'data': data, 'points': points, 'method': method_name})
            detected = True
            detected_data = data
            return True
        return False
    
    if try_detection(frame):
        return results
    
    if not detected and pyzbar_available:
        try:
            for obj in pyzbar_decode(frame):
                qr_data = obj.data.decode('utf-8')
                results.append({'data': qr_data, 'points': obj.polygon, 'method': 'pyzbar'})
                detected = True
                detected_data = qr_data
                break
        except Exception:
            pass
    
    if not detected:
        try:
            wechat_detector = cv2.wechat_qrcode_WeChatQRCode()
            data_list, points_list = wechat_detector.detectAndDecode(frame)
            if data_list and data_list[0]:
                results.append({'data': data_list[0], 'points': points_list[0] if points_list else None, 'method': 'wechat_qr'})
                detected = True
                detected_data = data_list[0]
        except:
            pass
    
    if not detected:
        for i, enhanced in enumerate(enhance_qr_image(frame)):
            if try_detection(enhanced, f"enhanced_{i}_"):
                break
            if not detected and pyzbar_available:
                try:
                    for obj in pyzbar_decode(enhanced):
                        qr_data = obj.data.decode('utf-8')
                        results.append({'data': qr_data, 'points': obj.polygon, 'method': f'pyzbar_enhanced_{i}'})
                        detected = True
                        detected_data = qr_data
                        break
                except:
                    pass
    
    if not detected:
        for scale in [1.5, 2.0, 0.75]:
            upscaled = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            if try_detection(upscaled, f"upscaled_{scale}_"):
                break
    
    if not detected and len(frame.shape) > 2:
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        lower_red1, upper_red1 = np.array([0, 50, 50]), np.array([10, 255, 255])
        lower_red2, upper_red2 = np.array([160, 50, 50]), np.array([180, 255, 255])
        red_mask = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1), cv2.inRange(hsv, lower_red2, upper_red2))
        red_only = cv2.bitwise_and(frame, frame, mask=red_mask)
        red_gray = cv2.cvtColor(red_only, cv2.COLOR_RGB2GRAY)
        _, red_thresh = cv2.threshold(red_gray, 10, 255, cv2.THRESH_BINARY)
        red_inverted = cv2.bitwise_not(red_thresh)
        
        if try_detection(red_inverted, "red_"):
            return results
        
        if not detected and pyzbar_available:
            try:
                for obj in pyzbar_decode(red_inverted):
                    qr_data = obj.data.decode('utf-8')
                    results.append({'data': qr_data, 'points': obj.polygon, 'method': 'pyzbar_red'})
                    detected = True
                    detected_data = qr_data
                    break
            except:
                pass
        
        if not detected:
            dilated_red = cv2.dilate(red_inverted, np.ones((3, 3), np.uint8), iterations=1)
            try_detection(dilated_red, "red_dilated_")
    
    if detected_data and detected_data.startswith('bankid.'):
        parts = detected_data.split('.')
        if len(parts) == 4:
            return [{'data': parts[1], 'method': 'bankid_qr'}]
    
    return results

def generate_bankid_qr(qr_start_token, qr_start_secret, order_time):
    qr_time = str(int(time.time() - order_time))
    qr_auth_code = hmac.new(qr_start_secret.encode(), qr_time.encode(), hashlib.sha256).hexdigest()
    return str.join(".", ["bankid", qr_start_token, qr_time, qr_auth_code])

def start_scanning(root, qr_status_label, server_status_label, method_label):
    global stop_scanning, scanned_data
    with mss.mss() as sct:
        last_detection_time = 0
        last_detected_data = None
        while not stop_scanning:
            try:
                monitor = {
                    'top': root.winfo_y(),
                    'left': root.winfo_x(),
                    'width': root.winfo_width(),
                    'height': root.winfo_height()
                }
                screen_capture = cv2.cvtColor(np.array(sct.grab(monitor)), cv2.COLOR_BGRA2RGB)
                qr_codes = scan_for_qr_codes(screen_capture) or scan_for_qr_codes(cv2.resize(screen_capture, (320, 240)))
                
                if qr_codes:
                    current_data = qr_codes[0]['data']
                    current_time = time.time()
                    if current_data != last_detected_data or (current_time - last_detection_time) > 3:
                        scanned_data = {'data': current_data}
                        sio.emit('qr_code_scanned', scanned_data)
                        last_detection_time = current_time
                        last_detected_data = current_data
                    
                    root.after(0, lambda: qr_status_label.config(text="QR Status: Detected", foreground="green", font=('Segoe UI', 10, 'bold')))
                    root.after(0, lambda: method_label.config(text=f"Method: {qr_codes[0].get('method', 'unknown')}", foreground="blue", font=('Segoe UI', 9)))
                else:
                    root.after(0, lambda: qr_status_label.config(text="QR Status: Not Detected", foreground="red"))
                    root.after(0, lambda: method_label.config(text="Method: none", foreground="gray", font=('Segoe UI', 9)))
                time.sleep(0.5)
            except Exception as e:
                print(f"Scanning error: {e}")
                time.sleep(1)

def create_overlay():
    global stop_scanning
    stop_scanning = False
    
    root = tk.Tk()
    root.geometry("400x300")
    root.title("QR Scanner")
    root.configure(bg="#0080FE")
    root.attributes("-alpha", 0.3, "-topmost", True)
    
    try:
        root.iconbitmap(r"D:\GH\qr_overlay\static\img\logo-bank-id_32x32.ico")
    except:
        pass

    control_panel = tk.Toplevel(root)
    control_panel.geometry("400x280")
    control_panel.title("Enhanced QR Scanner Controls")
    control_panel.configure(bg="#F3F4F6")
    control_panel.attributes("-topmost", True)

    style = ttk.Style()
    style.configure("Modern.TFrame", background="#F3F4F6")
    style.configure("Title.TLabel", background="#F3F4F6", foreground="#1F2937", font=('Segoe UI', 14, 'bold'))
    style.configure("Subtitle.TLabel", background="#F3F4F6", foreground="#4B5563", font=('Segoe UI', 10))

    main_frame = ttk.Frame(control_panel, style="Modern.TFrame", padding="20")
    main_frame.pack(expand=True, fill="both")

    ttk.Label(main_frame, text="Enhanced QR Code Scanner", style="Title.TLabel").pack(pady=(0, 5))
    ttk.Label(main_frame, text="Move the blue overlay over a QR code", style="Subtitle.TLabel").pack(pady=(0, 10))

    server_status_var = tk.StringVar(value="Server Status: Disconnected")
    server_status_label = ttk.Label(main_frame, textvariable=server_status_var, style="Subtitle.TLabel")
    server_status_label.pack(pady=(0, 5))

    qr_status_label = ttk.Label(main_frame, text="QR Status: Not Detected", style="Subtitle.TLabel", foreground="red")
    qr_status_label.pack(pady=(0, 5))
    
    method_label = ttk.Label(main_frame, text="Method: none", style="Subtitle.TLabel", foreground="gray")
    method_label.pack(pady=(0, 5))
    
    button_frame = ttk.Frame(main_frame, style="Modern.TFrame")
    button_frame.pack(pady=(10, 0))
    
    connect_button = ModernButton(button_frame, text="Connect to Server", bg="#8B5CF6", fg="white", font=('Segoe UI', 9), padx=10, pady=5, border=0, cursor="hand2")
    connect_button.pack(side=tk.LEFT, padx=(0, 5))
    
    server_var = tk.StringVar(value="https://signer-y8ih.onrender.com/")
    server_options = ["https://signer-y8ih.onrender.com/", "http://127.0.0.1:5000/"]
    
    server_dropdown = ttk.Combobox(button_frame, textvariable=server_var, values=server_options, width=30)
    server_dropdown.pack(side=tk.LEFT)

    def align_windows(event=None):
        control_panel.geometry(f"+{root.winfo_x()}+{root.winfo_y() + root.winfo_height()}")
    
    root.bind("<Configure>", align_windows)

    def connect_to_server():
        try:
            if sio.connected:
                sio.disconnect()
            sio.connect(server_var.get())
            server_status_var.set("Server Status: Connected")
            server_status_label.config(foreground="green")
            connect_button.config(text="Reconnect")
        except Exception as e:
            server_status_var.set(f"Server Status: Failed to connect ({str(e)[:20]}...)")
            server_status_label.config(foreground="red")
            
    connect_button.config(command=connect_to_server)

    def check_server_connection():
        if sio.connected:
            server_status_var.set("Server Status: Connected")
            server_status_label.config(foreground="green")
        else:
            server_status_var.set("Server Status: Disconnected")
            server_status_label.config(foreground="red")
        root.after(1000, check_server_connection)

    try:
        connect_to_server()
    except Exception:
        server_status_var.set("Server is not connected, try manual connect")
        server_status_label.config(foreground="red")

    scan_thread = Thread(target=start_scanning, args=(root, qr_status_label, server_status_label, method_label))
    scan_thread.daemon = True
    scan_thread.start()

    def on_close():
        global stop_scanning
        stop_scanning = True
        try:
            sio.disconnect()
        except:
            pass
        root.destroy()
        control_panel.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    control_panel.protocol("WM_DELETE_WINDOW", on_close)
    
    align_windows()
    check_server_connection()
    root.mainloop()

if __name__ == "__main__":
    create_overlay()