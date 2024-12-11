from flask import Flask, jsonify
import time
import sys
import RPi.GPIO as GPIO
from hx711 import HX711
from threading import Thread, Event

app = Flask(__name__)

# Configuração do sensor HX711
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
referenceUnit = -23.71
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()  # Tara feita uma vez no início
print("Tara concluída, pronto para adicionar peso!")

# Variáveis globais
weight = 0
stop_event = Event()

# Função para leitura contínua do peso
def read_weight():
    global weight
    while not stop_event.is_set():
        try:
            weight = hx.get_weight(9)
            print(weight)  # Mostra o peso no terminal
            hx.power_down()
            hx.power_up()
            time.sleep(0.01)  # Intervalo de 0,05 segundos
        except (KeyboardInterrupt, SystemExit):
            cleanAndExit()

# Função para limpar GPIO e encerrar o programa
def cleanAndExit():
    print("A limpar...")
    GPIO.cleanup()
    print("Processo finalizado!")
    sys.exit()

# Rota da API para obter o peso
@app.route('/peso', methods=['GET'])
def get_weight():
    return jsonify({"peso": weight})  # Devolve o peso em JSON

# Início do programa principal
if __name__ == '__main__':
    # Inicia a thread para leitura do peso
    thread = Thread(target=read_weight)
    thread.start()
    try:
        # Inicia o servidor Flask sem reiniciar
        app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
    finally:
        # Encerra a leitura contínua e limpa recursos
        stop_event.set()
        thread.join()
        cleanAndExit()