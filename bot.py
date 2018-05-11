import logging
import time
import RPi.GPIO as GPIO

from bluetooth import *

btSock    = None
port      = 0
isRunning = False

BOARD_NUM = 11
DELAY     = 1
UUID      = "84cc6419-0ead-4ed5-a03f-c31c3c58ff27"

# logging.basicConfig(filename='log.txt', filemode='w', level=logging.DEBUG)

def init():
    logging.basicConfig(filename='/spool/log.txt', filemode='w', level=logging.DEBUG)
    log('Running Initialization...')
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(BOARD_NUM, GPIO.OUT)
    log('Initialization Complete')

def log(text, level=''):
    print(text)
    if level == 'warning':
        logging.warning(text)
    elif level == 'error':
        logging.error(text)
    else:
        logging.info(text)

def init_bt_sock():
    global btSock, port, UUID

    # Set up bluetooth socket
    log('Creating Bluetooth Socket')
    btSock = BluetoothSocket(RFCOMM)
    btSock.bind(("", PORT_ANY))
    btSock.listen(1)
    
    # Set up bluetooth port
    port = btSock.getsockname()[1]
    log('Socket bound to port {}'.format(port))

    log('Attempting to create advertisment service')
    while True:
        try:
            advertise_service( btSock,
                "Raspberry Pi",
                service_id=UUID,
                service_classes=[ UUID, SERIAL_PORT_CLASS ],
                profiles=[ SERIAL_PORT_PROFILE ])
            break;
        except:
            time.sleep(1)
    log('Advertising service {}'.format(UUID))

def cleanup():
    log('Cleaning up GPIO...')
    GPIO.cleanup()
    log('Cleanup complete')

def toggle_button():
    global BOARD_NUM, DELAY
    
    log('Toggling GPIO')
    GPIO.output(BOARD_NUM, GPIO.HIGH)
    time.sleep(DELAY)
    GPIO.output(BOARD_NUM, GPIO.LOW)

def start():
    global isRunning, btSock

    isRunning = True
    
    while isRunning:
        try:
            init_bt_sock()
            log('Waiting for connection...')
            client_sock, client_info = btSock.accept()
            log('Connection from {}'.format(client_info))
            receive_data(client_sock, run_command)
            log('Closing client socket')
            client_sock.close()
            log('Closing Bluetooth socket')
            btSock.close()
            log('Socket closed')
    
        except IOError as e:
            log(e, 'error')
            isRunning = False
        except KeyboardInterrupt:
            log('Keyboard interrupt, disconnecting', 'warning')
            isRunning = False


def receive_data(client_sock, callback):
    try:
        # Will block until data is received or connection is closed
        log('Waiting for data...')
        data = client_sock.recv(1024)
        if len(data) == 0: return
        log('Data Received \"{}\"'.format(data))
        callback(data)
    except BluetoothError as e:
        log('Critical Error: \"{}\"'.format(e))
        return

def run_command(data):
    if data == 'go':
        toggle_button()

if __name__ == "__main__":
    try:
        init()
        start()
    finally:
        cleanup()
