import subprocess
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO
import eventlet
import time
import base64

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app)

# 백그라운드에서 ffmpeg 실행 → 프레임 추출 → WebSocket 전송
def stream_camera():
    # MJPEG 스트림 생성 (ffmpeg 사용)
    command = [
        'ffmpeg',
        '-f', 'video4linux2',
        '-i', '/dev/video0',
        '-vf', 'scale=320:240',
        '-f', 'mjpeg',
        '-q:v', '5',
        '-update', '1',
        'pipe:1'
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=0)

    while True:
        frame_data = b''
        while True:
            byte = process.stdout.read(1)
            if not byte:
                break
            frame_data += byte
            if frame_data.endswith(b'\xff\xd9'):  # JPEG EOI
                break

        if frame_data:
            b64_image = base64.b64encode(frame_data).decode('utf-8')
            socketio.emit('frame', {'image': b64_image})
        time.sleep(0.05)  # 조절 가능 (실시간 속도)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print("Client connected")

if __name__ == '__main__':
    threading.Thread(target=stream_camera, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
