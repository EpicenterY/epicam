from flask import Flask, render_template, Response, send_from_directory, request
import subprocess, threading, time, os
from datetime import datetime

app = Flask(__name__)

# 상태 변수
timelapse_running = False
timelapse_interval = 5  # 기본 5초
capture_dir = "captured"
os.makedirs(capture_dir, exist_ok=True)

# 타임랩스 캡처 루프
def capture_timelapse():
    global timelapse_running
    while timelapse_running:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(capture_dir, f"img_{timestamp}.jpg")
        subprocess.run([
            "libcamera-still",
            "-o", filename,
            "-t", "1",
            "--width", "640",
            "--height", "480",
            "--nopreview"
        ])
        time.sleep(timelapse_interval)

# 실시간 프레임 생성기
def generate_frames():
    while True:
        subprocess.run([
            "libcamera-jpeg",
            "-o", "/tmp/live.jpg",
            "-t", "1",
            "-n",
            "--width", "320",
            "--height", "240"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            with open("/tmp/live.jpg", "rb") as f:
                frame = f.read()
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except FileNotFoundError:
            continue
        time.sleep(0.2)  # 과도한 CPU 사용 방지

# 기본 페이지
@app.route('/')
def index():
    return render_template("index.html")

# 실시간 스트리밍 라우트
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# 타임랩스 시작
@app.route('/start_timelapse', methods=['POST'])
def start_timelapse():
    global timelapse_running, timelapse_interval
    interval = request.form.get('interval', '5')
    try:
        timelapse_interval = max(1, int(interval))
    except ValueError:
        timelapse_interval = 5

    if not timelapse_running:
        timelapse_running = True
        threading.Thread(target=capture_timelapse, daemon=True).start()
    return ("", 204)

# 타임랩스 중지
@app.route('/stop_timelapse', methods=['POST'])
def stop_timelapse():
    global timelapse_running
    timelapse_running = False
    return ("", 204)

# GIF 생성
@app.route('/generate_gif', methods=['POST'])
def generate_gif():
    output = os.path.join("static", "timelapse.gif")
    subprocess.run([
        "convert",
        "-delay", "20", "-loop", "0",
        f"{capture_dir}/*.jpg",
        output
    ])
    return ("", 204)

# GIF 다운로드
@app.route('/download_gif')
def download_gif():
    return send_from_directory("static", "timelapse.gif", as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
