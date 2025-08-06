from flask import Flask, render_template, Response, send_from_directory
import subprocess, threading, time, os
from datetime import datetime

app = Flask(__name__)
timelapse_running = False
capture_dir = "captured"
os.makedirs(capture_dir, exist_ok=True)

# 타임랩스 촬영 스레드
def capture_timelapse():
    while timelapse_running:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(capture_dir, f"img_{timestamp}.jpg")
        subprocess.run([
            "libcamera-still", "-o", filename, "-t", "1", "--width", "640", "--height", "480", "--nopreview"
        ])
        time.sleep(5)

# 실시간 영상 프레임 생성
@app.route('/video_feed')
def video_feed():
    def generate_frames():
        while True:
            subprocess.run([
                "libcamera-jpeg", "-o", "/tmp/live.jpg", "-t", "1", "--width", "640", "--height", "480", "--nopreview"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open("/tmp/live.jpg", "rb") as f:
                frame = f.read()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

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
    output = os.path.join("static", "timelapse.gif")
    subprocess.run([
        "convert", "-delay", "20", "-loop", "0",
        f"{capture_dir}/*.jpg", output
    ])
    return ("", 204)

@app.route('/download_gif')
def download_gif():
    return send_from_directory("static", "timelapse.gif", as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
