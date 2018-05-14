import logging
import time
import RPi.GPIO as GPIO

from bluetooth import *

bt_sock    = None
port       = None
is_running = False

BUTTON_BOARD_NUM = 11
LED_BOARD_NUM    = 16

DATA_LEN = 1024

BUTTON_DELAY = 1
LED_DELAY    = 5
RESET_DELAY  = 7

UUID = "84cc6419-0ead-4ed5-a03f-c31c3c58ff27"

# TODO: Add Security

#region Initialization

def init():
    """
    Initialize GPIO and Event Logger
    """
    global BUTTON_BOARD_NUM, LED_BOARD_NUM

    dt = datetime.datetime.now().strftime("%B %d %Y %I:%M %p")
    file_name = '/tmp/{} Go+ Bot.txt'.format(dt)
    logging.basicConfig(filename=file_name, filemode='w', level=logging.DEBUG)
    log('Log file created')
    log('Running Initialization...')
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(BUTTON_BOARD_NUM, GPIO.OUT)
    GPIO.setup(LED_BOARD_NUM, GPIO.OUT)
    log('Initialization Complete')

def init_bt_sock():
    """
    Initialize Bluetooth socket.
    """
    global bt_sock, port, UUID

    # Set up Bluetooth socket
    log('Creating Bluetooth Socket')
    bt_sock = BluetoothSocket(RFCOMM)
    bt_sock.bind(("", PORT_ANY))
    bt_sock.listen(1)

    # Set up bluetooth port
    port = bt_sock.getsockname()[1]
    log('Socket bound to port {}'.format(port))

    log('Attempting to create advertisement service')
    try:
        advertise_service(bt_sock,
                          "Raspberry Pi",
                          service_id=UUID,
                          service_classes=[UUID, SERIAL_PORT_CLASS],
                          profiles=[SERIAL_PORT_PROFILE])
    except:
        log('Fatal Error: Bluetooth Service not initialized')
    log('Advertising service {}'.format(UUID))
    # Inform user that bluetooth is ready to connect
    toggle_led()

#endregion

#region Clean up

def cleanup():
    """
    Clean up the GPIO
    """
    log('Cleaning up GPIO...')
    GPIO.cleanup()
    log('Cleanup complete')

#endregion

#region Functions
def log(text, level=''):
    """
    Log the given message
    :param text: text to log
    :param level: type of log
    """
    print(text)
    if level == 'warning':
        logging.warning(text)
    elif level == 'error':
        logging.error(text)
    else:
        logging.info(text)

def receive_data(client_sock, callback):
    """
    Receive Data from Client
    """
    global DATA_LEN
    try:
        # Will block until data is received or connection is closed
        log('Waiting for data...')
        data = client_sock.recv(DATA_LEN)
        if len(data) == 0:
            return
        log('Data Received \"{}\"'.format(data))
        callback(data)
    except BluetoothError as e:
        log('Critical Error: \"{}\"'.format(e))

def run_command(data):
    """
    Parse and run the command
    """
    if data == 'go':
        toggle_button()
    elif data == 'reset':
        reset_go_plus()

def start():
    """
    Start the bluetooth server socket
    """
    global is_running, bt_sock

    is_running = True

    while is_running:
        try:
            init_bt_sock()
            log('Waiting for connection...')
            client_sock, client_info = bt_sock.accept()
            log('Connection from {}'.format(client_info))
            receive_data(client_sock, run_command)
            log('Command Received and processed.. closing client socket')
            client_sock.close()
            log('Closing Bluetooth socket')
            bt_sock.close()
            log('Socket closed')

        except IOError as e:
            log(e, 'error')
            is_running = False
        except KeyboardInterrupt:
            log('Keyboard interrupt, disconnecting', 'warning')
            is_running = False
#endregion

#region GPIO Toggling

def reset_go_plus():
    """
    Run the push sequence to reset the Go+
    """
    global BUTTON_BOARD_NUM, RESET_DELAY
    log('Resetting Go+')
    GPIO.output(BUTTON_BOARD_NUM, GPIO.HIGH)
    time.sleep(RESET_DELAY)
    GPIO.output(BUTTON_BOARD_NUM, GPIO.LOW)
    time.sleep(.5)
    GPIO.output(BUTTON_BOARD_NUM, GPIO.HIGH)
    time.sleep(RESET_DELAY)
    GPIO.output(BUTTON_BOARD_NUM, GPIO.LOW)

def toggle_button():
    """
    Toggle the GPIO to push the Go+'s button.
    """
    global BUTTON_BOARD_NUM, BUTTON_DELAY
    
    log('Toggling GPIO')
    GPIO.output(BUTTON_BOARD_NUM, GPIO.HIGH)
    time.sleep(BUTTON_DELAY)
    GPIO.output(BUTTON_BOARD_NUM, GPIO.LOW)

def toggle_led():
    """
    Toggle the GPIO pin to inform the user that the bluetooth socket
    is now listening for incoming connections.
    """
    global LED_BOARD_NUM, LED_DELAY

    log('Toggling LED')
    GPIO.output(LED_BOARD_NUM, GPIO.HIGH)
    time.sleep(LED_DELAY)
    GPIO.output(LED_BOARD_NUM, GPIO.LOW)

#endregion

if __name__ == "__main__":
    try:
        init()
        start()
    finally:
        cleanup()
