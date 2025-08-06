from flask import Flask, Response
from picamera2 import Picamera2
from PIL import Image
import io
import time

app = Flask(__name__)

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

def generate_frames():
    while True:
        frame = picam2.capture_array()
        img = Image.fromarray(frame)
        stream = io.BytesIO()
        img.save(stream, format='JPEG')
        jpeg = stream.getvalue()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')
        time.sleep(0.05)  # 약 20fps

@app.route('/')
def index():
    return '<h2>Raspberry Pi CCTV</h2><img src="/video_feed">'

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
