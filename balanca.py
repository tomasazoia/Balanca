import io
import logging
import socketserver
from http import server
from threading import Condition
import threading
from hx711 import HX711
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import time
import sys
import RPi.GPIO as GPIO

# Página HTML com valor dinâmico da balança
PAGE = """\
<html>
<head>
<title>Picamera2 MJPEG Streaming Demo</title>
</head>
<body>
<h1>Picamera2 MJPEG Streaming Demo</h1>
<p>Valor da Balança: <span id="weight">Carregando...</span> g</p>
<img src="stream.mjpg" width="640" height="480" />
<script>
    // Função para atualizar o valor da balança dinamicamente
    function updateWeight() {
        fetch('/weight')
            .then(response => response.text())
            .then(data => {
                document.getElementById('weight').innerText = data;
            });
    }
    setInterval(updateWeight, 1000);  // Atualiza o valor a cada 1 segundo
</script>
</body>
</html>
"""

# Classe para o output do streaming MJPEG
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

# Classe que vai lidar com as requisições HTTP
class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path == '/weight':  # Rota para retornar o valor da balança
            weight = str(current_weight)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', len(weight))
            self.end_headers()
            self.wfile.write(weight.encode('utf-8'))
        else:
            self.send_error(404)
            self.end_headers()

# Classe do servidor HTTP para streaming
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# Configuração da câmera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))

# Configuração da balança HX711
hx = HX711(dout_pin=5, pd_sck_pin=6)
hx.set_reading_format("MSB", "MSB")
referenceUnit = -23.71  # Ajuste de calibração baseado no peso conhecido
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()

# Variável global para armazenar o valor atual da balança
current_weight = 0.0

# Função para ler os valores da balança periodicamente
def read_weight():
    global current_weight
    while True:
        current_weight = hx.get_weight(5)
        time.sleep(1)

# Inicia a thread para ler o peso da balança
weight_thread = threading.Thread(target=read_weight, daemon=True)
weight_thread.start()

# Inicia o servidor HTTP
try:
    address = ('', 7123)
    server = StreamingServer(address, StreamingHandler)
    print("Servidor iniciado na porta 7123")
    server.serve_forever()
finally:
    picam2.stop_recording()
