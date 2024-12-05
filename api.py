from flask import Flask, jsonify
import time
import sys
import RPi.GPIO as GPIO
from hx711 import HX711
from threading import Thread, Event

app = Flask(__name__)

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
referenceUnit = -23.71
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()

print("Tare done! Add weight now...")

weight = 0
stop_event = Event()

def read_weight():
    global weight
    while not stop_event.is_set():
        try:
            weight = hx.get_weight(5)
            print(weight)  # Imprime o valor na consola
            hx.power_down()
            hx.power_up()
            time.sleep(0.1)
        except (KeyboardInterrupt, SystemExit):
            cleanAndExit()

def cleanAndExit():
    print("Cleaning...")
    GPIO.cleanup()
    print("Bye!")
    sys.exit()

@app.route('/peso', methods=['GET'])
def get_weight():
    return jsonify({"weight": weight})

if __name__ == '__main__':
    thread = Thread(target=read_weight)
    thread.start()
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    finally:
        stop_event.set()
        thread.join()
        cleanAndExit()