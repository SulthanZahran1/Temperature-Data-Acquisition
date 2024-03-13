import sys
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit, QFileDialog, QHBoxLayout
from PyQt6.QtCore import QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
# import random
import re
from datetime import datetime
import serial
import serial.tools.list_ports
from PyQt6.QtGui import QFont
import time
from threading import Lock

# Initialize the serial port variable to None (it will be set later)
serial_port_working = None

# Create a global lock for serial port access
serial_lock = Lock()


class SerialConnectionThread(QThread):
    connection_success = pyqtSignal(str)
    connection_failed = pyqtSignal(str)

    def __init__(self, baud_rate, timeout):
        super().__init__()
        self.baud_rate = baud_rate
        self.timeout = timeout

    def run(self):
        found = False  # Initialize found flag as False

        for port_info in serial.tools.list_ports.comports():
            serial_port = port_info.device
            
            try:
                with serial.Serial(serial_port, self.baud_rate, timeout=self.timeout, write_timeout=self.timeout+3) as temp_conn:
                    temp_conn.flushInput()
                    temp_conn.flushOutput()
                    print(temp_conn)
                    
                    # Initialize success flag for write/read operations
                    success = False
                    
                    # Retry loop - try to write and read up to 3 times
                    for attempt in range(5):
                        try:
                            time.sleep(0.01)
                            temp_conn.write(b'*S#')
                            time.sleep(0.01)
                            response = temp_conn.readline().decode('utf-8').strip()
                            
                            if re.match(r'\*\d+#', response):
                                found = True  # Suitable device found
                                success = True  # Write/read operations successful
                                self.connection_success.emit(serial_port)
                                temp_conn.close()  # Ensure the serial connection is closed on exit
                                break  # Exit retry loop upon success
                        except (serial.SerialTimeoutException, serial.SerialException) as e:
                            # Handle possible write/read exceptions here
                            print(f"Error on attempt {attempt + 1}: {e}")
                        
                        if success:
                            break  # Exit the retry loop if successful
                        
                    if found:
                        break  # Exit the with block if a suitable device has been found
            except serial.SerialException as e:
                # Log or handle the error without stopping the loop
                print(f"Attempted to open {serial_port}, but failed: {e}")
                continue  # Try the next port

        if not found:
            # If the loop completes without finding a device, emit the failure signal
            self.connection_failed.emit("Arduino gagal ditemukan!")


class DataReaderWorker(QObject):
    data_ready = pyqtSignal(float)  # Signal to emit the average temperature
    finished = pyqtSignal()  # Signal to indicate completion

    def __init__(self, serial_connection):
        super().__init__()
        self.serial_connection = serial_port_working

    def read_data_average(self, iterations=2):
        total_temp = 0
        valid_readings = 0
        for _ in range(iterations):
            # Assume read_data is a method that reads data from the serial port
            temp_reading = self.read_data(self.serial_connection)
            try:
                temp_reading = float(temp_reading)
                total_temp += temp_reading
                valid_readings += 1
            except (ValueError, TypeError):
                continue  # Skip invalid readings

        if valid_readings > 0:
            average_temp = total_temp / valid_readings
        else:
            average_temp = 0  # Handle error or no data case

        self.data_ready.emit(average_temp)  # Emit the average temperature
        self.finished.emit()  # Indicate that the work is done

    def read_data(self, serial_conn):
        global serial_lock
        with serial_lock:  # Acquire the lock
            try:
                if serial_conn and serial_conn.is_open:
                    serial_conn.write(b'*S#')  # Send command to request data
                    # Wait for data to become available
                    response = self.non_blocking_readline(serial_conn)
                    if response.startswith('*') and response.endswith('#'):
                        return response[1:-1]  # Return the valid data
                    else:
                        return 0  # Invalid response format
            except serial.SerialException as e:
                print(f"Serial communication error: {e}")
                return 0
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return 0
    
    def non_blocking_readline(self, serial_conn, timeout=0.3):
        end_time = time.time() + timeout
        line = bytearray()
        while time.time() < end_time:
            if serial_conn.in_waiting > 0:
                
                char = serial_conn.read(1)
                line += char
                if char == b'\n':  # Check if the newline character is received
                    break
            # Without sleep, this loop will aggressively check in_waiting, potentially consuming more CPU.
        return line.decode('utf-8').strip()  # Decode and return the line


class TemperatureDataAcquisitionSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_lock = Lock()  # Initialize the lock

        self.setWindowTitle("Temperature Data Acquisition System")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        self.serial_conn = None
        self.temperature_data = []  # Initialize as empty list
        self.plot_data = []  # Store data points for plotting
        self.update_job = None
        
        self.update_timer = QTimer(self)  # Create a QTimer instance
        self.update_timer.timeout.connect(self.acquire_and_plot_data)  # Connect timeout signal to the slot
        

    
        self.initUI()
        
    def initUI(self):
        # Main layout
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.layout = QVBoxLayout(self.centralWidget)

        # Header
        self.header_label = QLabel("Temperature Data Acquisition System", self)
        self.layout.addWidget(self.header_label)

        # Current Temperature Display
        self.temp_display = QLabel("--- °C", self)
        self.layout.addWidget(self.temp_display)
        self.temp_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(150)  # Sets the font size to 18 points. Adjust the size as needed.
        self.temp_display.setFont(font)

        # Plot Area
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Assuming self.layout is your QVBoxLayout
        # Control Panel with QHBoxLayout
        control_panel_layout = QHBoxLayout()

        # Customize button font size
        button_font = QFont()
        button_font.setPointSize(50)  # Increase font size here
        
        # Control Panel
        self.start_button = QPushButton("MULAI", self)
        self.start_button.clicked.connect(self.start_update)
        self.start_button.setFont(button_font)
        # self.layout.addWidget(self.start_button)
        self.start_button.setMinimumSize(100, 100)  # Set minimum size (width, height)

        self.stop_button = QPushButton("SELESAI", self)
        self.stop_button.clicked.connect(self.stop_update)
        self.stop_button.setFont(button_font)
        self.stop_button.setMinimumSize(100, 100)

        self.save_button = QPushButton("SIMPAN DATA", self)
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setFont(button_font)
        # self.layout.addWidget(self.save_button)
        self.save_button.setMinimumSize(100, 100)

        # Add buttons to the QHBoxLayout
        control_panel_layout.addWidget(self.start_button)
        control_panel_layout.addWidget(self.stop_button)
        control_panel_layout.addWidget(self.save_button)

        # Add the QHBoxLayout to the main QVBoxLayout
        self.layout.addLayout(control_panel_layout)

        # Logs
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Grafik Temperatur terhadap Waktu')
        self.ax.set_xlabel('Waktu (detik)')
        self.ax.set_ylabel('Temperatur (°C)')
        
    def acquire_and_plot_data(self):
        # Create the worker and thread
        self.data_reader_thread = QThread()
        self.data_reader_worker = DataReaderWorker(serial_port_working)
        self.data_reader_worker.moveToThread(self.data_reader_thread)

        # Connect signals
        self.data_reader_worker.data_ready.connect(self.handle_data_ready)
        self.data_reader_worker.finished.connect(self.data_reader_thread.quit)
        self.data_reader_thread.started.connect(self.data_reader_worker.read_data_average)

        # Start the thread
        self.data_reader_thread.start()
        
    def handle_data_ready(self, average_temperature):
        # Calibration results
        calibrated_temp = (0.3015250701388389 * average_temperature - 21.798755485216873)-85
        # calibrated_temp = ((calibrated_temp-110)/(220-110))*(55-25)+25
        batch_value = 10
        calibrated_temp = average_temperature

        # Add calibrated temperature to the list
        self.temperature_data.append(calibrated_temp)

        # Display the temperature with 2 decimal places
        self.temp_display.setText(f"{calibrated_temp:.2f} °C")

        # Determine current time in seconds since start
        elapsed_time = (datetime.now() - self.start_time).total_seconds()

        # Calculate the index for the current batch (0 for the first 100, 1 for the next 100, etc.)
        batch_index = len(self.temperature_data) // batch_value

        # Calculate running average for the current batch
        current_batch_start = batch_index * batch_value
        current_batch_data = self.temperature_data[current_batch_start:]
        if len(current_batch_data) > 0:  # Ensure we have data to avoid division by zero
            running_avg_temp = sum(current_batch_data) / len(current_batch_data)

            # Ensure there's a plot data point for each batch, including the current incomplete one
            if len(self.plot_data) <= batch_index:
                self.plot_data.append((elapsed_time, running_avg_temp))
            else:
                self.plot_data[batch_index] = (elapsed_time, running_avg_temp)

        # Update the plot with the latest data
        self.update_plot()

    def update_plot(self):
        # Ensure to clear only the necessary parts of the plot for efficiency
        self.ax.cla()  # Clear the current axes
        self.ax.set_title('Temperature Over Time')
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Temperature (°C)')
        # self.ax.set_ylim(0, 100)
        
        if self.plot_data:
            x_data, y_data = zip(*self.plot_data)
            self.ax.plot(x_data, y_data, '-o', label='Average Temperature')
            self.ax.legend()

        self.canvas.draw()

    def start_update(self):
        self.log_message("Mencoba mencari arduino, mohon menunggu!")
        self.connection_thread = SerialConnectionThread(baud_rate=9600, timeout=1)
        self.connection_thread.connection_success.connect(self.on_connection_success)
        self.connection_thread.connection_failed.connect(self.on_connection_failed,)
        self.connection_thread.start()
        
    def on_connection_success(self, port):
        time.sleep(3)
        global serial_port_working
        serial_port_working = serial.Serial(port, 9600, timeout=1, write_timeout=1)
        self.log_message(f"Koneksi dibuka pada port {port}.")
        if not hasattr(self, 'start_time'):
            self.start_time = datetime.now()
        self.update_timer.start(1000)  # Start the timer with this interval
        
        self.log_message("Pengukuran temperatur mulai")

    def on_connection_failed(self, message):
        self.log_message(message)

    def stop_update(self):
        self.update_timer.stop()  # Stop the timer
        self.log_message("Pengukuran temperatur selesai")
        self.close_serial_connection()
    
    def close_serial_connection(self):
        global serial_port_working
        if serial_port_working:
            serial_port_working.close()
            self.log_message("Serial connection closed.")
            
    def read_data(self, serial_conn):
        print(serial_conn)
        try:
            if serial_conn and serial_conn.is_open:
                serial_conn.write(b'*S#')
                response = serial_conn.readline().decode('utf-8').strip()
                print(f"Raw response: {response}")

                if response.startswith('*') and response.endswith('#'):
                    return response[1:-1]  # Return the valid data
                else:
                    return "Invalid response received: " + response
            else:
                return "Serial connection is not open."
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def read_data_average(self, iterations=10):
        total_temp = 0
        valid_readings = 0

        for _ in range(iterations):
            temp_reading = self.read_data(serial_port_working)
            time.sleep(2)
            # temp_reading = 0
            try:
                # Convert the reading to float and accumulate it
                temp_reading = float(temp_reading)
                print(temp_reading)
                total_temp += temp_reading
                valid_readings += 1
            except ValueError:
                # Handle the case where the reading cannot be converted to float
                # You might want to log this as an error or handle it in some way
                print("Invalid reading received")
            except TypeError:
                print("NaN value")

        # Calculate the average if there were any valid readings
        if valid_readings > 0:
            new_temp = total_temp / valid_readings
        else:
            # Handle the case where no valid readings were received
            new_temp = 0  # or some other default/error value

        return new_temp

    def save_data(self):
        # Directly call getSaveFileName without using options
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "CSV Files (*.csv);;All Files (*)")
        if fileName:
            with open(fileName, "w") as file:
                file.write("Waktu (s),Temperatur (Celcius)\n")
                for interval, temp in self.plot_data:
                    file.write(f"{interval},{temp:.2f}\n")
            self.log_message(f"Data disimpan ke {fileName}")

    def log_message(self, message):
        self.log_text.append(message)


def main():
    app = QApplication(sys.argv)
    ex = TemperatureDataAcquisitionSystem()
    ex.showMaximized()  # This will show the window maximized
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
