import time
import sys
import cv2  # Biblioteca OpenCV para capturar a câmera
from hx711 import HX711

def cleanAndExit():
    print("Cleaning...")
    print("Bye!")
    sys.exit()

# Função para capturar imagem quando um peso específico for detectado
def capture_image():
    # Inicializa a captura da câmera
    cap = cv2.VideoCapture(0)  # Use '0' para a câmera padrão
    if not cap.isOpened():
        print("Erro ao abrir a câmera.")
        return
    
    ret, frame = cap.read()
    if ret:
        # Salva a imagem capturada
        cv2.imwrite("peso_detectado.jpg", frame)
        print("Imagem capturada e salva como 'peso_detectado.jpg'")
    else:
        print("Erro ao capturar imagem.")
    
    cap.release()

# Conexão: DAT no GPIO 5 e CLK no GPIO 6
hx = HX711(dout_pin=5, pd_sck_pin=6)

# Configuração de leitura
hx.set_reading_format("MSB", "MSB")  # Usando MSB como padrão

# Definir o novo referenceUnit (ajustado conforme o cálculo)
referenceUnit = -23.71  # Valor calculado com base no peso do iPhone 11
hx.set_reference_unit(referenceUnit)

# Reset e tara
hx.reset()
hx.tare()

print("Tara feita! Agora, coloque um peso conhecido na balança.")

# Peso a ser detectado para capturar a imagem (por exemplo, 200g)
peso_desejado = 200  # Você pode ajustar esse valor conforme necessário

while True:
    try:
        # Lê o peso da balança
        val = hx.get_weight(5)
        print(f"Peso: {val:.2f} g")  # Exibindo o peso com duas casas decimais
        
        # Verifica se o peso está perto do valor desejado (por exemplo, 200g)
        if abs(val - peso_desejado) < 10:  # Ajuste a tolerância conforme necessário
            print("Peso detectado. Capturando imagem...")
            capture_image()  # Captura a imagem

        time.sleep(0.5)

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
