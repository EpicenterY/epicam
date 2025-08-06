from flask import Flask, render_template, Response, send_from_directory
import cv2, threading, time, os, subprocess

app = Flask(__name__)
camera = cv2.VideoCapture(0)

# 타임랩스 관련
timelapse_running = False
captured_dir = "captured"
os.makedirs(captured_dir, exist_ok=True)

def capture_timelapse():
    count = 0
    while timelapse_running:
        filename = os.path.join(captured_dir, f"img_{count:04d}.jpg")
        subprocess.run(["fswebcam", "-r", "640x480", filename])
        count += 1
        time.sleep(5)  # 5초 간격

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_timelapse', methods=['POST'])
def start_timelapse():
    global timelapse_running
    if not timelapse_running:
        timelapse_running = True
        threading.Thread(target=capture_timelapse, daemon=True).start()
    return ("", 204)

@app.route('/stop_timelapse', methods=['POST'])
def stop_timelapse():
    global timelapse_running
    timelapse_running = False
    return ("", 204)

@app.route('/generate_gif', methods=['POST'])
def generate_gif():
    gif_path = os.path.join("static", "timelapse.gif")
    subprocess.run([
        "convert", "-delay", "20", "-loop", "0",
        os.path.join(captured_dir, "img_*.jpg"),
        gif_path
    ])
    return ("", 204)

@app.route('/download_gif')
def download_gif():
    return send_from_directory("static", "timelapse.gif", as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
