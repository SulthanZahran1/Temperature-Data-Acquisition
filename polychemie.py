import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

# Maximum number of data points to display
max_points = 50

# Function to update the plot
def update_plot():
    # Simulate acquiring new temperature data
    new_temp = random.uniform(15, 25)
    temperature_data.append(new_temp)
    temp_display.config(text=f"{new_temp:.2f} °C")

    # Keep the list of temperature data within the max_points limit
    if len(temperature_data) > max_points:
        del temperature_data[0]

    # Clear the plot, plot the data, and draw
    ax.clear()
    ax.plot(temperature_data, '-o', markersize=4)
    ax.set_ylim(10, 30)  # Adjust y-axis limits as needed
    canvas.draw()

    # Schedule the next update
    root.after(1000, update_plot)

# Initial temperature data
temperature_data = [20]

# Create the main window
root = tk.Tk()
root.title("Temperature Data Acquisition System")

# Header Section
header_label = tk.Label(root, text="Temperature Data Acquisition System", font=("Arial", 16))
header_label.pack(pady=10)

# Data Display Area
data_frame = ttk.Frame(root)
data_frame.pack(pady=10)

current_temp_label = ttk.Label(data_frame, text="Current Temperature:", font=("Arial", 12))
current_temp_label.grid(row=0, column=0, padx=10)

temp_display = ttk.Label(data_frame, text="--- °C", font=("Arial", 12))
temp_display.grid(row=0, column=1, padx=10)

# Plot Area
fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Control Panel
control_frame = ttk.Frame(root)
control_frame.pack(pady=10)

start_button = ttk.Button(control_frame, text="Start", command=lambda: update_plot())
start_button.grid(row=0, column=0, padx=10)

stop_button = ttk.Button(control_frame, text="Stop", command=lambda: root.after_cancel(update_plot))
stop_button.grid(row=0, column=1, padx=10)

save_button = ttk.Button(control_frame, text="Save Data")
save_button.grid(row=0, column=2, padx=10)

# Status Bar
status_bar = ttk.Label(root, text="Status: Idle", relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

# Logging Area
log_label = ttk.Label(root, text="Logs", font=("Arial", 12))
log_label.pack(pady=10)

log_frame = ttk.Frame(root)
log_frame.pack(pady=10)

log_text = tk.Text(log_frame, height=5, width=50)
log_text.grid(row=0, column=0, padx=10)
log_scroll = ttk.Scrollbar(log_frame, command=log_text.yview)
log_scroll.grid(row=0, column=1, sticky='nsew')
log_text['yscrollcommand'] = log_scroll.set

root.mainloop()
