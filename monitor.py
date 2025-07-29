import hid
import struct
import time
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np

class ProControllerIMU:
    def __init__(self):
        self.device = None
        self.running = False
        self.packet_counter = 0
        
        # Nintendo Switch Pro Controller VID/PID
        self.VID = 0x057E
        self.PID = 0x2009
        
        # Data storage for plotting
        self.max_samples = 5000  # Maximum number of samples to display
        self.accel_data = {
            'x': deque(maxlen=self.max_samples),
            'y': deque(maxlen=self.max_samples),
            'z': deque(maxlen=self.max_samples)
        }
        self.gyro_data = {
            'x': deque(maxlen=self.max_samples),
            'y': deque(maxlen=self.max_samples),
            'z': deque(maxlen=self.max_samples)
        }
        self.timestamps = deque(maxlen=self.max_samples)
        self.start_time = time.time()
        
        # Thread safety
        self.data_lock = threading.Lock()
        
        # Plotting setup
        self.fig = None
        self.axes = None
        self.lines = {}
        
    def connect(self):
        """Connect to the Pro Controller"""
        try:
            # Find and open the Pro Controller
            device_info = hid.enumerate(self.VID, self.PID)
            if not device_info:
                print("Nintendo Switch Pro Controller not found!")
                return False
            
            self.device = hid.device()
            self.device.open(self.VID, self.PID)
            self.device.set_nonblocking(1)
            
            print(f"Connected to: {device_info[0]['product_string']}")
            
            # Initialize the controller
            if not self.initialize_controller():
                return False
                
            return True
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def send_command(self, command, data=None):
        """Send a command to the controller"""
        if data is None:
            data = []
        
        # Build the packet: [0x80, counter, command, data...]
        packet = [0x80, self.packet_counter & 0xFF, command] + data
        
        # Pad to 64 bytes
        while len(packet) < 64:
            packet.append(0x00)
        
        try:
            self.device.write(packet)
            self.packet_counter += 1
            time.sleep(0.01)  # Small delay between commands
            return True
        except Exception as e:
            print(f"Failed to send command: {e}")
            return False
    
    def initialize_controller(self):
        """Initialize the controller and enable IMU"""
        print("Initializing controller...")
        
        # Enable standard input reports
        if not self.send_command(0x03, [0x30]):
            print("Failed to set input report mode")
            return False
        
        time.sleep(0.1)
        
        # Enable IMU
        if not self.send_command(0x40, [0x01]):
            print("Failed to enable IMU")
            return False
        
        time.sleep(0.1)
        
        print("Controller initialized successfully")
        print("IMU enabled")
        return True
    
    def parse_imu_data(self, data):
        """Parse IMU data from the input report"""
        try:
            # IMU data starts at byte 13 and contains 3 samples
            imu_samples = []
            
            for i in range(3):  # 3 IMU samples per report
                offset = 13 + (i * 12)  # Each IMU sample is 12 bytes
                
                if offset + 12 <= len(data):
                    # Extract accelerometer data (6 bytes)
                    accel_x = struct.unpack('<h', bytes(data[offset:offset+2]))[0]
                    accel_y = struct.unpack('<h', bytes(data[offset+2:offset+4]))[0]
                    accel_z = struct.unpack('<h', bytes(data[offset+4:offset+6]))[0]
                    
                    # Extract gyroscope data (6 bytes)
                    gyro_x = struct.unpack('<h', bytes(data[offset+6:offset+8]))[0]
                    gyro_y = struct.unpack('<h', bytes(data[offset+8:offset+10]))[0]
                    gyro_z = struct.unpack('<h', bytes(data[offset+10:offset+12]))[0]
                    
                    imu_samples.append({
                        'accel': (accel_x, accel_y, accel_z),
                        'gyro': (gyro_x, gyro_y, gyro_z)
                    })
            
            return imu_samples
            
        except Exception as e:
            print(f"Error parsing IMU data: {e}")
            return []
    
    def add_imu_sample(self, accel, gyro):
        """Add a new IMU sample to the data storage"""
        with self.data_lock:
            current_time = time.time() - self.start_time
            
            # Add timestamp
            self.timestamps.append(current_time)
            
            # Add accelerometer data
            self.accel_data['x'].append(accel[0])
            self.accel_data['y'].append(accel[1])
            self.accel_data['z'].append(accel[2])
            
            # Add gyroscope data
            self.gyro_data['x'].append(gyro[0])
            self.gyro_data['y'].append(gyro[1])
            self.gyro_data['z'].append(gyro[2])
    
    def setup_plot(self):
        """Setup the matplotlib figure and axes"""
        plt.style.use('dark_background')
        self.fig, self.axes = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.suptitle('Nintendo Switch Pro Controller IMU Data', fontsize=16, color='white')
        
        # Setup accelerometer plot
        self.axes[0].set_title('Accelerometer Data', fontsize=14, color='white')
        self.axes[0].set_ylabel('Acceleration (raw)', fontsize=12, color='white')
        self.axes[0].grid(True, alpha=0.3)
        self.axes[0].set_facecolor('black')
        
        # Setup gyroscope plot
        self.axes[1].set_title('Gyroscope Data', fontsize=14, color='white')
        self.axes[1].set_xlabel('Time (seconds)', fontsize=12, color='white')
        self.axes[1].set_ylabel('Angular Velocity (raw)', fontsize=12, color='white')
        self.axes[1].grid(True, alpha=0.3)
        self.axes[1].set_facecolor('black')
        
        # Initialize line objects with different colors
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        labels_accel = ['Accel X', 'Accel Y', 'Accel Z']
        labels_gyro = ['Gyro X', 'Gyro Y', 'Gyro Z']
        
        # Create lines for accelerometer
        for i, (axis, color, label) in enumerate(zip(['x', 'y', 'z'], colors[:3], labels_accel)):
            line, = self.axes[0].plot([], [], color=color, linewidth=2, label=label, alpha=0.8)
            self.lines[f'accel_{axis}'] = line
        
        # Create lines for gyroscope
        for i, (axis, color, label) in enumerate(zip(['x', 'y', 'z'], colors[3:], labels_gyro)):
            line, = self.axes[1].plot([], [], color=color, linewidth=2, label=label, alpha=0.8)
            self.lines[f'gyro_{axis}'] = line
        
        # Add legends
        self.axes[0].legend(loc='upper right', facecolor='black', edgecolor='white')
        self.axes[1].legend(loc='upper right', facecolor='black', edgecolor='white')
        
        # Adjust layout
        plt.tight_layout()
        
        return self.fig
    
    def animate(self, frame):
        """Animation function for matplotlib"""
        with self.data_lock:
            if len(self.timestamps) < 2:
                return list(self.lines.values())
            
            # Convert deques to lists for plotting
            times = list(self.timestamps)
            
            # Calculate time window (last 10 seconds)
            max_time = max(times)
            min_time = max_time - 10
            
            # Find indices for the time window
            window_indices = [i for i, t in enumerate(times) if t >= min_time]
            
            if not window_indices:
                return list(self.lines.values())
            
            # Get windowed data
            windowed_times = [times[i] for i in window_indices]
            
            # Update accelerometer lines with windowed data
            for axis in ['x', 'y', 'z']:
                accel_data_list = list(self.accel_data[axis])
                windowed_accel = [accel_data_list[i] for i in window_indices]
                self.lines[f'accel_{axis}'].set_data(windowed_times, windowed_accel)
            
            # Update gyroscope lines with windowed data
            for axis in ['x', 'y', 'z']:
                gyro_data_list = list(self.gyro_data[axis])
                windowed_gyro = [gyro_data_list[i] for i in window_indices]
                self.lines[f'gyro_{axis}'].set_data(windowed_times, windowed_gyro)
            
            # Update axis limits
            if windowed_times:
                # Set time axis limits
                for ax in self.axes:
                    ax.set_xlim(min_time, max_time)
                
                # Y-axis limits for accelerometer (based on windowed data)
                all_windowed_accel = []
                for axis in ['x', 'y', 'z']:
                    accel_data_list = list(self.accel_data[axis])
                    windowed_accel = [accel_data_list[i] for i in window_indices]
                    all_windowed_accel.extend(windowed_accel)
                
                if all_windowed_accel:
                    accel_min, accel_max = min(all_windowed_accel), max(all_windowed_accel)
                    accel_range = accel_max - accel_min
                    margin = max(accel_range * 0.1, 100)  # At least 100 units margin
                    self.axes[0].set_ylim(accel_min - margin, accel_max + margin)
                
                # Y-axis limits for gyroscope (based on windowed data)
                all_windowed_gyro = []
                for axis in ['x', 'y', 'z']:
                    gyro_data_list = list(self.gyro_data[axis])
                    windowed_gyro = [gyro_data_list[i] for i in window_indices]
                    all_windowed_gyro.extend(windowed_gyro)
                
                if all_windowed_gyro:
                    gyro_min, gyro_max = min(all_windowed_gyro), max(all_windowed_gyro)
                    gyro_range = gyro_max - gyro_min
                    margin = max(gyro_range * 0.1, 100)  # At least 100 units margin
                    self.axes[1].set_ylim(gyro_min - margin, gyro_max + margin)
        
        return list(self.lines.values())

    
    def read_loop(self):
        """Main reading loop"""
        print("Starting IMU data reading...")
        print("Check the graph window for real-time visualization")
        print("-" * 50)
        
        sample_count = 0
        
        while self.running:
            try:
                data = self.device.read(64)
                
                if data and len(data) >= 49:  # Minimum length for IMU data
                    # Check if this is a standard input report (0x30)
                    if data[0] == 0x30:
                        imu_samples = self.parse_imu_data(data)
                        
                        for sample in imu_samples:
                            accel = sample['accel']
                            gyro = sample['gyro']
                            
                            # Add sample to data storage for plotting
                            self.add_imu_sample(accel, gyro)
                            
                            # Print every 30th sample to avoid spam
                            if sample_count % 30 == 0:
                                print(f"Sample {sample_count:5d}: "
                                      f"A({accel[0]:6d},{accel[1]:6d},{accel[2]:6d}) | "
                                      f"G({gyro[0]:6d},{gyro[1]:6d},{gyro[2]:6d})")
                            
                            sample_count += 1
                
                time.sleep(0.001)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                if self.running:  # Only print error if we're supposed to be running
                    print(f"Error reading data: {e}")
                    break
    
    def start_reading(self):
        """Start the IMU data reading in a separate thread"""
        if not self.device:
            print("Not connected to controller")
            return False
        
        self.running = True
        self.read_thread = threading.Thread(target=self.read_loop)
        self.read_thread.daemon = True
        self.read_thread.start()
        return True
    
    def start_plotting(self):
        """Start the real-time plotting"""
        fig = self.setup_plot()
        ani = animation.FuncAnimation(fig, self.animate, interval=50, blit=False, cache_frame_data=False)
        return ani
    
    def stop_reading(self):
        """Stop reading IMU data"""
        self.running = False
        if hasattr(self, 'read_thread'):
            self.read_thread.join(timeout=1.0)
    
    def disconnect(self):
        """Disconnect from the controller"""
        self.stop_reading()
        
        if self.device:
            try:
                # Disable IMU before disconnecting
                self.send_command(0x40, [0x00])
                time.sleep(0.1)
                self.device.close()
                print("Disconnected from controller")
            except Exception as e:
                print(f"Error during disconnect: {e}")

def main():
    controller = ProControllerIMU()
    
    try:
        if not controller.connect():
            return
        
        if not controller.start_reading():
            return
        
        print("Starting real-time IMU visualization...")
        print("Move your Pro Controller to see the data change!")
        print("Close the graph window or press Ctrl+C to stop")
        
        # Start the real-time plotting
        ani = controller.start_plotting()
        
        # Show the plot (this will block until the window is closed)
        plt.show()
            
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()
