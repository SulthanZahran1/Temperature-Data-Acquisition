import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
import random

class TemperaturePlotter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Temperature Data Viewer')
        self.setGeometry(100, 100, 800, 600)

        self.temperature_data = []  # Store raw temperature data
        self.plot_data = []  # Store data points for plotting
        self.start_time = datetime.now()  # Record start time

        # Plotting setup
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        
        # Timer setup for data simulation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.simulate_new_data)
        self.timer_interval = 500  # Time in milliseconds
        
        self.batch_number = 0  # Track the current batch number

        # UI setup
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Temperature display
        self.temp_display = QLabel("Temperature: 0.00 °C", self)
        
        # Start and Stop buttons for data simulation
        btn_start_simulation = QPushButton('Start Simulation', self)
        btn_start_simulation.clicked.connect(self.start_simulation)

        btn_stop_simulation = QPushButton('Stop Simulation', self)
        btn_stop_simulation.clicked.connect(self.stop_simulation)

        # Add widgets to layout
        layout.addWidget(self.canvas)
        layout.addWidget(self.temp_display)
        layout.addWidget(btn_start_simulation)
        layout.addWidget(btn_stop_simulation)

        # Initial plot setup
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Temperature Over Time')
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Temperature (°C)')


    def handle_data_ready(self, average_temperature):
        # Calibration results
        # calibrated_temp = 0.3015250701388389 * average_temperature - 21.798755485216873
        calibrated_temp = average_temperature

        # Add calibrated temperature to the list
        self.temperature_data.append(calibrated_temp)

        # Display the temperature with 2 decimal places
        self.temp_display.setText(f"{calibrated_temp:.2f} °C")

        # Determine current time in seconds since start
        elapsed_time = (datetime.now() - self.start_time).total_seconds()

        # Calculate the index for the current batch (0 for the first 100, 1 for the next 100, etc.)
        batch_index = len(self.temperature_data) // 100

        # Calculate running average for the current batch
        current_batch_start = batch_index * 100
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
        self.ax.set_ylim(0,100)
        
        if self.plot_data:
            x_data, y_data = zip(*self.plot_data)
            self.ax.plot(x_data, y_data, '-o', label='Average Temperature')
            self.ax.legend()

        self.canvas.draw()



    def simulate_new_data(self):
        # Determine the batch we're currently generating data for
        self.batch_number = len(self.temperature_data) // 100

        # Cycle through different mean values for each batch by changing the range of generated temperatures
        if self.batch_number % 4 == 0:
            new_temp = random.uniform(1, 20)  # These numbers will average to a lower value
        elif self.batch_number % 4 == 1:
            new_temp = random.uniform(30, 50)  # Average around 40
        elif self.batch_number % 4 == 2:
            new_temp = random.uniform(50, 70)  # Average around 60
        else:
            new_temp = random.uniform(80, 100)  # These will average to a higher value

        self.handle_data_ready(new_temp)


    def start_simulation(self):
        self.timer.start(self.timer_interval)  # Start the timer to call simulate_new_data every 0.5 seconds

    def stop_simulation(self):
        self.timer.stop()  # Stop the timer


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TemperaturePlotter()
    ex.show()
    sys.exit(app.exec())
