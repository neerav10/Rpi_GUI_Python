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

# --------------------------
# GPIO and sensor setup
# --------------------------
DHT_PIN = 17               # DHT11 data pin
GAS_DO_PIN = 27            # MQ sensor digital output
ULTRASONIC_TRIG = 23       # HC-SR04 trigger
ULTRASONIC_ECHO = 24       # HC-SR04 echo

DHT_SENSOR = Adafruit_DHT.DHT11

GPIO.setmode(GPIO.BCM)
GPIO.setup(GAS_DO_PIN, GPIO.IN)
GPIO.setup(ULTRASONIC_TRIG, GPIO.OUT)
GPIO.setup(ULTRASONIC_ECHO, GPIO.IN)

# --------------------------
# CSV file setup
# --------------------------
filename = "essentials_log.csv"
file_lock = threading.Lock()   # lock to prevent race conditions on file access

# Write header if file is empty
with file_lock:
    try:
        with open(filename, mode='r') as f:
            if f.read(1):
                pass  # file not empty
            else:
                raise FileNotFoundError
    except (FileNotFoundError, IOError):
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "TEMP", "PPM", "LEVEL", "Anomaly"])

# --------------------------
# Ultrasonic sensor reading function
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
# CSV reading function for plotting
# --------------------------
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

# --------------------------
# Main Application Class
# --------------------------
class SensorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sensor Monitoring and Visualization")

        # Threshold variables
        self.temp_threshold = tk.DoubleVar(value=50)
        self.gas_threshold = tk.IntVar(value=1)

        # Data containers for live display
        self.times = []
        self.temps = []
        self.gas_values = []
        self.levels = []

        # Configure Matplotlib Figure and Axes (3 subplots)
        self.fig, self.axs = plt.subplots(3, 1, figsize=(8, 6), sharex=True)
        self.fig.tight_layout(pad=3)

        # Tkinter canvas for Matplotlib figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=6, padx=10, pady=10)

        # Temperature slider and label
        ttk.Label(root, text="Temperature Threshold (°C)").grid(row=1, column=0, sticky="w", padx=10)
        self.temp_slider = ttk.Scale(root, from_=0, to=100, orient='horizontal', variable=self.temp_threshold, command=self.update_temp_label)
        self.temp_slider.grid(row=1, column=1, sticky="ew", padx=(0,5))
        self.temp_value_label = ttk.Label(root, text=f"{self.temp_threshold.get():.1f}")
        self.temp_value_label.grid(row=1, column=2, sticky="w")

        # Gas slider and label
        ttk.Label(root, text="Gas Threshold (PPM, 0 or 1)").grid(row=1, column=3, sticky="w", padx=10)
        self.gas_slider = ttk.Scale(root, from_=0, to=1, orient='horizontal', variable=self.gas_threshold, command=self.update_gas_label)
        self.gas_slider.grid(row=1, column=4, sticky="ew", padx=(0,5))
        self.gas_value_label = ttk.Label(root, text=f"{int(self.gas_threshold.get())}")
        self.gas_value_label.grid(row=1, column=5, sticky="w")

        # Status label for faults
        self.status_label = ttk.Label(root, text="", font=("Arial", 14))
        self.status_label.grid(row=2, column=0, columnspan=6, pady=10)

        # Start periodic updates
        self.update_plots()
        self.start_sensor_thread()

        # Handle window close
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    # Update temperature label when slider moves
    def update_temp_label(self, event=None):
        self.temp_value_label.config(text=f"{self.temp_threshold.get():.1f}")

    # Update gas label when slider moves
    def update_gas_label(self, event=None):
        self.gas_value_label.config(text=f"{int(round(self.gas_threshold.get()))}")

    def start_sensor_thread(self):
        self.sensor_thread = threading.Thread(target=self.sensor_loop, daemon=True)
        self.sensor_thread.start()

    def sensor_loop(self):
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Read DHT11
            humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
            temp_val = temperature if temperature is not None else "N/A"

            # Read MQ gas sensor (DO pin LOW means gas detected)
            gas_state = GPIO.input(GAS_DO_PIN)
            gas_detected = (gas_state == 0)
            ppm_val = 1 if gas_detected else 0

            # Read ultrasonic sensor
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

            # Append to CSV with thread-safe lock
            with file_lock:
                with open(filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([timestamp, temp_val, ppm_val, level_val, anomaly])

            # Update internal data for plotting
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            self.times.append(dt)
            self.temps.append(float(temp_val) if temp_val != "N/A" else None)
            self.gas_values.append(ppm_val)
            self.levels.append(float(level_val) if level_val != "N/A" else None)

            # Keep only last 100 records to limit memory usage
            max_len = 100
            if len(self.times) > max_len:
                self.times = self.times[-max_len:]
                self.temps = self.temps[-max_len:]
                self.gas_values = self.gas_values[-max_len:]
                self.levels = self.levels[-max_len:]

            time.sleep(0.5)  # Adjust read frequency as needed

    def update_plots(self):
        # Clear plots
        for ax in self.axs:
            ax.clear()

        # Plot temperature
        if self.times and any(t is not None for t in self.temps):
            temps_clean = [t if t is not None else float('nan') for t in self.temps]
            self.axs[0].plot(self.times, temps_clean, 'r-', label='Temperature (°C)')
        self.axs[0].axhline(self.temp_threshold.get(), color='r', linestyle='--', label='Temp Threshold')
        self.axs[0].set_ylabel("Temperature (°C)")
        self.axs[0].legend(loc='upper right')
        self.axs[0].grid(True)

        # Plot gas ppm
        if self.times:
            self.axs[1].step(self.times, self.gas_values, 'g-', label='Gas PPM')
        self.axs[1].axhline(self.gas_threshold.get(), color='g', linestyle='--', label='Gas Threshold')
        self.axs[1].set_ylabel("Gas PPM")
        self.axs[1].set_ylim(-0.1, 1.1)
        self.axs[1].legend(loc='upper right')
        self.axs[1].grid(True)

        # Plot level
        if self.times and any(l is not None for l in self.levels):
            levels_clean = [l if l is not None else float('nan') for l in self.levels]
            self.axs[2].plot(self.times, levels_clean, 'b-', label='Level (cm)')
        self.axs[2].set_ylabel("Level (cm)")
        self.axs[2].set_xlabel("Time")
        self.axs[2].legend(loc='upper right')
        self.axs[2].grid(True)

        self.fig.autofmt_xdate()
        self.canvas.draw()

        # Fault detection for latest sensor data
        fault_msg = ""
        if self.temps and self.gas_values and self.levels:
            last_temp = self.temps[-1]
            last_gas = self.gas_values[-1]
            last_level = self.levels[-1]

            if last_temp is None or last_level is None:
                fault_msg = "Critical fault: Sensor data missing!"
            else:
                if last_temp > self.temp_threshold.get() or last_gas > self.gas_threshold.get():
                    fault_msg = "Critical fault detected!"
                if last_level < 0 or last_level > 400:
                    fault_msg = "Critical fault detected!"

        self.status_label.config(text=fault_msg, foreground='red' if fault_msg else 'green')

        # Schedule next GUI update
        self.root.after(1000, self.update_plots)

    def on_close(self):
        GPIO.cleanup()
        self.root.destroy()

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = SensorApp(root)
    root.mainloop()
