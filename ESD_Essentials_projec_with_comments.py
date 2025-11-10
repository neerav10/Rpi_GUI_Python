## @file sensor_monitor_gui.py
#  @brief A real-time GUI-based multi-sensor monitoring system for Raspberry Pi.
#  @details
#  This program interfaces with a DHT11 temperature sensor, MQ gas sensor, and HC-SR04 ultrasonic sensor.
#  Data are continuously read, logged into a CSV file, and visualized in a Tkinter-based GUI with Matplotlib.
#  Threshold levels for temperature and gas concentration can be dynamically adjusted using sliders.
#  Anomalies and faults are automatically detected and displayed on the GUI.
#
#  @author
#  Neerav Desai & U.K. Shobbiga 
#
#  @date
#  November 2025
#
#  @par Hardware Connections:
#  - *DHT11* → GPIO 17  
#  - *MQ Gas Sensor* (DO pin) → GPIO 27  
#  - *Ultrasonic Sensor* → TRIG = GPIO 23, ECHO = GPIO 24  
#
#  @see
#  - Adafruit_DHT Python Library
#  - Raspberry Pi GPIO documentation
#
#  @ingroup RaspberryPi_Monitoring_GUI

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import RPi.GPIO as GPIO
import Adafruit_DHT
import time
import csv
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import threading

# ===============================================================
#                   GPIO AND SENSOR CONFIGURATION
# ===============================================================

## @brief DHT11 data pin
DHT_PIN = 17
## @brief MQ Gas Sensor digital output pin
GAS_DO_PIN = 27
## @brief Ultrasonic sensor TRIG pin
ULTRASONIC_TRIG = 23
## @brief Ultrasonic sensor ECHO pin
ULTRASONIC_ECHO = 24
## @brief Sensor type for DHT
DHT_SENSOR = Adafruit_DHT.DHT11

# GPIO mode and pin setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(GAS_DO_PIN, GPIO.IN)
GPIO.setup(ULTRASONIC_TRIG, GPIO.OUT)
GPIO.setup(ULTRASONIC_ECHO, GPIO.IN)

# ===============================================================
#                   CSV FILE INITIALIZATION
# ===============================================================

## @brief CSV filename for data logging
filename = "essentials_log.csv"

## @brief Thread lock to synchronize file access
file_lock = threading.Lock()

# @brief Initialize CSV file with header if empty
with file_lock:
    try:
        with open(filename, mode='r') as f:
            if f.read(1):
                pass
            else:
                raise FileNotFoundError
    except (FileNotFoundError, IOError):
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "TEMP", "PPM", "LEVEL", "Anomaly"])

# ===============================================================
#                   SENSOR READING FUNCTIONS
# ===============================================================

## @brief Reads distance (in cm) from the HC-SR04 ultrasonic sensor.
#  @return Distance in centimeters (float), or None if timeout occurs.
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


## @brief Reads data from the CSV log file.
#  @return Four lists containing timestamps, temperature, gas, and level data.
def read_csv_data():
    times, temps, gas_values, levels = [], [], [], []
    with file_lock:
        try:
            with open(filename, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        times.append(datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S"))
                        temps.append(float(row["TEMP"]) if row["TEMP"] != "N/A" else None)
                        gas_values.append(int(row["PPM"]))
                        levels.append(float(row["LEVEL"]) if row["LEVEL"] != "N/A" else None)
                    except Exception:
                        continue
        except FileNotFoundError:
            pass
    return times, temps, gas_values, levels


# ===============================================================
#                   MAIN APPLICATION CLASS
# ===============================================================

## @class SensorApp
#  @brief A GUI application for real-time visualization and monitoring of sensor data.
#  @details
#  This class creates a Tkinter window embedding live-updating Matplotlib plots
#  for temperature, gas concentration, and water level readings.  
#  It also continuously logs sensor data into a CSV file using a background thread.
#
#  @par Responsibilities:
#  - Acquire and log sensor data.
#  - Dynamically plot readings in real-time.
#  - Provide fault/anomaly detection.
#  - Allow runtime adjustment of sensor thresholds.

class SensorApp:
    ## @brief Constructor for initializing the GUI layout and logic.
    #  @param root The main Tkinter window.
    def _init_(self, root):
        self.root = root
        self.root.title("Sensor Monitoring and Visualization")

        # Threshold variables
        self.temp_threshold = tk.DoubleVar(value=50)
        self.gas_threshold = tk.IntVar(value=1)

        # Data containers for live updates
        self.times = []
        self.temps = []
        self.gas_values = []
        self.levels = []

        # ---------------- GUI Configuration ----------------
        self.fig, self.axs = plt.subplots(3, 1, figsize=(8, 6), sharex=True)
        self.fig.tight_layout(pad=3)

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=6, padx=10, pady=10)

        # Sliders and labels for thresholds
        ttk.Label(root, text="Temperature Threshold (°C)").grid(row=1, column=0, sticky="w", padx=10)
        self.temp_slider = ttk.Scale(root, from_=0, to=100, orient='horizontal', variable=self.temp_threshold, command=self.update_temp_label)
        self.temp_slider.grid(row=1, column=1, sticky="ew", padx=(0,5))
        self.temp_value_label = ttk.Label(root, text=f"{self.temp_threshold.get():.1f}")
        self.temp_value_label.grid(row=1, column=2, sticky="w")

        ttk.Label(root, text="Gas Threshold (PPM, 0 or 1)").grid(row=1, column=3, sticky="w", padx=10)
        self.gas_slider = ttk.Scale(root, from_=0, to=1, orient='horizontal', variable=self.gas_threshold, command=self.update_gas_label)
        self.gas_slider.grid(row=1, column=4, sticky="ew", padx=(0,5))
        self.gas_value_label = ttk.Label(root, text=f"{int(self.gas_threshold.get())}")
        self.gas_value_label.grid(row=1, column=5, sticky="w")

        self.status_label = ttk.Label(root, text="", font=("Arial", 14))
        self.status_label.grid(row=2, column=0, columnspan=6, pady=10)

        # Start live updates
        self.update_plots()
        self.start_sensor_thread()

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    ## @brief Updates temperature slider label.
    def update_temp_label(self, event=None):
        self.temp_value_label.config(text=f"{self.temp_threshold.get():.1f}")

    ## @brief Updates gas slider label.
    def update_gas_label(self, event=None):
        self.gas_value_label.config(text=f"{int(round(self.gas_threshold.get()))}")

    ## @brief Starts a background thread for continuous sensor data acquisition.
    def start_sensor_thread(self):
        self.sensor_thread = threading.Thread(target=self.sensor_loop, daemon=True)
        self.sensor_thread.start()

    ## @brief Sensor data acquisition loop (runs on a background thread).
    #  @details
    #  Reads DHT11, MQ gas sensor, and ultrasonic distance data periodically.
    #  Logs results to CSV and updates internal memory.
    def sensor_loop(self):
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
            temp_val = temperature if temperature is not None else "N/A"

            gas_state = GPIO.input(GAS_DO_PIN)
            gas_detected = (gas_state == 0)
            ppm_val = 1 if gas_detected else 0

            level = read_ultrasonic()
            level_val = level if level is not None else "N/A"

            # Simple anomaly detection logic
            anomaly = "No"
            if temp_val == "N/A" or level_val == "N/A":
                anomaly = "Yes"
            else:
                if not (0 <= temp_val <= 50) or not (0 <= level_val <= 400):
                    anomaly = "Yes"

            # Thread-safe CSV writing
            with file_lock:
                with open(filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([timestamp, temp_val, ppm_val, level_val, anomaly])

            # Data update
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            self.times.append(dt)
            self.temps.append(float(temp_val) if temp_val != "N/A" else None)
            self.gas_values.append(ppm_val)
            self.levels.append(float(level_val) if level_val != "N/A" else None)

            # Maintain buffer size
            max_len = 100
            if len(self.times) > max_len:
                self.times = self.times[-max_len:]
                self.temps = self.temps[-max_len:]
                self.gas_values = self.gas_values[-max_len:]
                self.levels = self.levels[-max_len:]

            time.sleep(0.5)

    ## @brief Updates live Matplotlib plots on the GUI.
    def update_plots(self):
        for ax in self.axs:
            ax.clear()

        # --- Temperature ---
        if self.times and any(t is not None for t in self.temps):
            temps_clean = [t if t is not None else float('nan') for t in self.temps]
            self.axs[0].plot(self.times, temps_clean, 'r-', label='Temperature (°C)')
        self.axs[0].axhline(self.temp_threshold.get(), color='r', linestyle='--', label='Temp Threshold')
        self.axs[0].set_ylabel("Temperature (°C)")
        self.axs[0].legend(loc='upper right')
        self.axs[0].grid(True)

        # --- Gas PPM ---
        if self.times:
            self.axs[1].step(self.times, self.gas_values, 'g-', label='Gas PPM')
        self.axs[1].axhline(self.gas_threshold.get(), color='g', linestyle='--', label='Gas Threshold')
        self.axs[1].set_ylabel("Gas PPM")
        self.axs[1].set_ylim(-0.1, 1.1)
        self.axs[1].legend(loc='upper right')
        self.axs[1].grid(True)

        # --- Ultrasonic Level ---
        if self.times and any(l is not None for l in self.levels):
            levels_clean = [l if l is not None else float('nan') for l in self.levels]
            self.axs[2].plot(self.times, levels_clean, 'b-', label='Level (cm)')
        self.axs[2].set_ylabel("Level (cm)")
        self.axs[2].set_xlabel("Time")
        self.axs[2].legend(loc='upper right')
        self.axs[2].grid(True)

        self.fig.autofmt_xdate()
        self.canvas.draw()

        # Fault detection and GUI update
        fault_msg = ""
        if self.temps and self.gas_values and self.levels:
            last_temp = self.temps[-1]
            last_gas = self.gas_values[-1]
            last_level = self.levels[-1]

            if last_temp is None or last_level is None:
                fault_msg = "Critical fault: Sensor data missing!"
            elif last_temp > self.temp_threshold.get() or last_gas > self.gas_threshold.get() or not (0 <= last_level <= 400):
                fault_msg = "Critical fault detected!"

        self.status_label.config(text=fault_msg, foreground='red' if fault_msg else 'green')
        self.root.after(1000, self.update_plots)

    ## @brief Handles cleanup when closing the GUI.
    def on_close(self):
        GPIO.cleanup()
        self.root.destroy()


# ===============================================================
#                   MAIN PROGRAM ENTRY POINT
# ===============================================================

## @brief Entry point for launching the GUI application.
if _name_ == "_main_":
    root = tk.Tk()
    app = SensorApp(root)
    root.mainloop()
