from flask import Flask, render_template, Response, jsonify
import cv2
import urllib.request
import numpy as np
from ultralytics import YOLO
import requests

app = Flask(__name__)

# URL do feed MJPEG (pode ser alterado conforme o IP do Raspberry Pi)
camera_url = 'http://192.168.23.112:7123/stream.mjpg'
model = YOLO('best.pt')  # Modelo treinado

# Dicionário de nomes de classes
class_names = ['Apple', 'Apricot', 'Banana', 'Beetroot', 'Black_Grapes', 'Broccoli', 'Cabbage', 'Carrot', 'Cauliflower', 'Cherry_Tomato_Red', 'Chinese_Cabbage', 'Crown_White_Pear', 'Cucumber', 'Fuji_Apple', 'Garlic', 'Granny_smith_apple', 'Grape_Fruit', 'Green_Bell_Pepper', 'Green_Chilli_Pepper', 'Green_zucchini', 'Hass_Avacado', 'Lemon', 'Lettuce', 'Lime', 'Mango', 'Melon', 'Meyer_Lemon', 'Nectarine_Peach', 'Onion_White', 'Orange', 'Peach', 'Pear_Williams_Rouge', 'Pink_Grapes', 'Pomegranate', 'Potato', 'Pumkin', 'Radish', 'RedBell_pepper', 'Red_Chilli', 'Red_Chilli_Pepper', 'Red_Onion', 'Red_Radish', 'Red_Tomato', 'Red_pomelo', 'Sweet_Corn', 'Sweet_potato', 'Watermelon', 'White_zucchini', 'Yellow_Bell_Pepper', 'Yellow_Cherry_Tomato', 'Yellow_Tomato', 'avacado', 'grapes', 'kiwi', 'pear', 'pink_plum', 'plum', 'pomelo', 'purple_plum']

def gen_frames():
    """Gera frames para o feed ao vivo a partir da URL do MJPEG."""
    stream = urllib.request.urlopen(camera_url)
    bytes = b''
    while True:
        bytes += stream.read(1024)
        a = bytes.find(b'\xff\xd8')  # frame starting
        b = bytes.find(b'\xff\xd9')  # frame ending
        if a != -1 and b != -1:
            jpg = bytes[a:b+2]
            bytes = bytes[b+2:]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Fornece o feed ao vivo da câmera."""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Recebe uma solicitação para capturar e analisar um frame."""
    stream = urllib.request.urlopen(camera_url)
    bytes = b''
    while True:
        bytes += stream.read(1024)
        a = bytes.find(b'\xff\xd8')  # frame starting
        b = bytes.find(b'\xff\xd9')  # frame ending
        if a != -1 and b != -1:
            jpg = bytes[a:b+2]
            bytes = bytes[b+2:]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            break

    if frame is None:
        return jsonify({"error": "Failed to capture image"}), 500

    # Executa a detecção
    results = model(frame)
    detected_classes = []
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls.item())  # Converte class_id para inteiro
            class_name = class_names[class_id]
            detected_classes.append(class_name)

    return jsonify(detected_classes)

@app.route('/weight')
def weight():
    """Obtém o peso da balança do Raspberry Pi."""
    raspberry_pi_ip = '192.168.23.112'
    url = f'http://{raspberry_pi_ip}:5001/peso'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return jsonify(data)
    else:
        return jsonify({"error": "Failed to get weight data"}), 500

@app.route('/')
def index():
    """Página inicial."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)