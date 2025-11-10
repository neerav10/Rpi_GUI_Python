import RPi.GPIO as GPIO
import time
import csv
from datetime import datetime
import Adafruit_DHT

# --------------------------
# GPIO pin setup
# --------------------------
DHT_PIN = 17               # DHT11 data pin
GAS_DO_PIN = 27            # MQ sensor digital output
ULTRASONIC_TRIG = 23       # HC-SR04 trigger
ULTRASONIC_ECHO = 24       # HC-SR04 echo

# DHT sensor type
DHT_SENSOR = Adafruit_DHT.DHT11

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(GAS_DO_PIN, GPIO.IN)
GPIO.setup(ULTRASONIC_TRIG, GPIO.OUT)
GPIO.setup(ULTRASONIC_ECHO, GPIO.IN)

# --------------------------
# CSV file setup
# --------------------------
filename = "raw_log.csv"
with open(filename, mode='a', newline='') as file:
    writer = csv.writer(file)
    if file.tell() == 0:
        writer.writerow(["Timestamp", "TEMP", "PPM", "LEVEL", "Anomaly"])

# --------------------------
# Function to read ultrasonic sensor
# --------------------------
def read_ultrasonic():
    GPIO.output(ULTRASONIC_TRIG, False)
    time.sleep(0.1)

    GPIO.output(ULTRASONIC_TRIG, True)
    time.sleep(0.00001)
    GPIO.output(ULTRASONIC_TRIG, False)

    pulse_start = time.time()
    timeout = pulse_start + 0.04
    while GPIO.input(ULTRASONIC_ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return None

    pulse_end = time.time()
    timeout = pulse_end + 0.04
    while GPIO.input(ULTRASONIC_ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return None

    pulse_duration = pulse_end - pulse_start
    distance_cm = pulse_duration * 17150
    return round(distance_cm, 2)

# --------------------------
# Main loop
# --------------------------
try:
    print("Starting sensor monitoring... Press Ctrl+C to stop.\n")
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Read DHT11
        humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
        temp_val = temperature if temperature is not None else "N/A"

        # Read MQ gas sensor (DO pin goes LOW when gas is detected)
        gas_state = GPIO.input(GAS_DO_PIN)
        gas_detected = (gas_state == 0)
        ppm_val = 1 if gas_detected else 0

        # Read ultrasonic distance
        level = read_ultrasonic()
        level_val = level if level is not None else "N/A"

        # Anomaly detection
        anomaly = "No"
        if temp_val == "N/A" or level_val == "N/A":
            anomaly = "Yes"
        else:
            if not (0 <= temp_val <= 50):
                anomaly = "Yes"
            if not (0 <= level_val <= 400):
                anomaly = "Yes"

        # Display to console
        gas_status = "Gas Detected" if gas_detected else "No Gas"
        print(f"[{timestamp}] TEMP: {temp_val}°C | GAS: {gas_status} | LEVEL: {level_val} cm | Sensor_Fault: {anomaly}")

        # Write to CSV
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, temp_val, ppm_val, level_val, anomaly])

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nMonitoring stopped by user.")

finally:
    GPIO.cleanup()
