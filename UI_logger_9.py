import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QComboBox, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
import time



def byte2_hex(string_1):
    hex_string_with_dashes = '-'.join(f'{byte:02x}' for byte in string_1)
    return hex_string_with_dashes

class UartLogger(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("UART Logger")
        self.setGeometry(100, 100, 600, 400)

        # Create layout
        layout = QVBoxLayout()

        # COM Port Selection
        com_layout = QHBoxLayout()
        com_label = QLabel("COM Port:")
        self.com_combobox = QComboBox()
        self.refresh_com_ports()
        com_layout.addWidget(com_label)
        com_layout.addWidget(self.com_combobox)
        layout.addLayout(com_layout)

        # Baud Rate Selection
        baud_layout = QHBoxLayout()
        baud_label = QLabel("Baud Rate:")
        self.baud_combobox = QComboBox()
        self.baud_combobox.addItems(["9600", "19200", "38400", "57600", "115200"])
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combobox)
        layout.addLayout(baud_layout)

        # Stop Bits Selection
        stopbits_layout = QHBoxLayout()
        stopbits_label = QLabel("Stop Bits:")
        self.stopbits_combobox = QComboBox()
        self.stopbits_combobox.addItems(["1", "1.5", "2"])
        stopbits_layout.addWidget(stopbits_label)
        stopbits_layout.addWidget(self.stopbits_combobox)
        layout.addLayout(stopbits_layout)

        # Parity Selection
        parity_layout = QHBoxLayout()
        parity_label = QLabel("Parity:")
        self.parity_combobox = QComboBox()
        self.parity_combobox.addItems(["None", "Even", "Odd", "Mark", "Space"])
        parity_layout.addWidget(parity_label)
        parity_layout.addWidget(self.parity_combobox)
        layout.addLayout(parity_layout)

        # Timeout Setting
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Timeout (m-seconds):")
        self.timeout_lineedit = QLineEdit()
        self.timeout_lineedit.setText("1")  # Default timeout value
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_lineedit)
        layout.addLayout(timeout_layout)

        # Validate Button
        self.validate_button = QPushButton("Connect")
        self.validate_button.clicked.connect(self.validate_settings)
        layout.addWidget(self.validate_button)

        # Disconnect Button
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect)
        self.disconnect_button.setEnabled(False)
        layout.addWidget(self.disconnect_button)

        # Text Area for UART Data
        self.uart_data_textedit = QTextEdit()
        self.uart_data_textedit.setReadOnly(True)
        self.uart_data_textedit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.uart_data_textedit.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.uart_data_textedit)

        # Set the layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def refresh_com_ports(self):
        ports = serial.tools.list_ports.comports()
        self.com_combobox.clear()
        self.com_combobox.addItems([port.device for port in ports])

    def validate_settings(self):
        com_port = self.com_combobox.currentText()
        baud_rate = self.baud_combobox.currentText()
        stop_bits = self.stopbits_combobox.currentText()
        parity = self.parity_combobox.currentText()
        self.timeout_value = float(self.timeout_lineedit.text())  # Store the timeout value

        stop_bits_dict = {
            "1": serial.STOPBITS_ONE,
            "1.5": serial.STOPBITS_ONE_POINT_FIVE,
            "2": serial.STOPBITS_TWO
        }

        parity_dict = {
            "None": serial.PARITY_NONE,
            "Even": serial.PARITY_EVEN,
            "Odd": serial.PARITY_ODD,
            "Mark": serial.PARITY_MARK,
            "Space": serial.PARITY_SPACE
        }

        try:
            self.serial_connection = serial.Serial(
                port=com_port,
                baudrate=int(baud_rate),
                stopbits=stop_bits_dict[stop_bits],
                parity=parity_dict[parity],
                timeout=1  # Use a fixed timeout for initial connection
            )
            self.uart_data_textedit.append("Settings are valid and connection established.")
            self.start_reading_uart()
            self.validate_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)

            # Disable the settings
            self.com_combobox.setEnabled(False)
            self.baud_combobox.setEnabled(False)
            self.stopbits_combobox.setEnabled(False)
            self.parity_combobox.setEnabled(False)
            self.timeout_lineedit.setEnabled(False)
        except Exception as e:
            self.uart_data_textedit.append(f"Error: {str(e)}")

    def start_reading_uart(self):
        self.read_thread = UartReadThread(self.serial_connection, self.timeout_value)
        self.read_thread.uart_data.connect(self.display_uart_data)
        self.read_thread.disconnected.connect(self.handle_disconnection)
        self.read_thread.start()

    def display_uart_data(self, data):
        self.uart_data_textedit.append(data)

    def disconnect(self):
        if hasattr(self, 'serial_connection') and self.serial_connection.is_open:
            self.serial_connection.close()
            self.uart_data_textedit.append("Disconnected from COM port.")
            self.validate_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)

            # Re-enable the settings
            self.com_combobox.setEnabled(True)
            self.baud_combobox.setEnabled(True)
            self.stopbits_combobox.setEnabled(True)
            self.parity_combobox.setEnabled(True)
            self.timeout_lineedit.setEnabled(True)

    def handle_disconnection(self):
        self.uart_data_textedit.append("COM port has been physically disconnected.")
        self.disconnect()

    def closeEvent(self, event):
        self.disconnect()
        event.accept()

    def show_context_menu(self, pos):
        menu = self.uart_data_textedit.createStandardContextMenu()
        clear_action = menu.addAction("Clear")
        action = menu.exec(self.uart_data_textedit.mapToGlobal(pos))
        if action == clear_action:
            self.uart_data_textedit.clear()

class UartReadThread(QThread):
    uart_data = pyqtSignal(str)
    disconnected = pyqtSignal()

    def __init__(self, serial_connection, timeout_value):
        super().__init__()
        self.serial_connection = serial_connection
        self.timeout_value = timeout_value / 1000 # Store the timeout value for use in the thread

    def run(self):
        R_start_time = 0
        received_data = bytearray()
        delta_time = time.time()
        while self.serial_connection.is_open:
            try:
                time.sleep(self.timeout_value / 2)
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    #print(self.serial_connection.in_waiting)
                    received_data.extend(data)
                    R_start_time = time.time()
                else:
                    if R_start_time > 0:
                        if time.time() - R_start_time > self.timeout_value:  # Use the stored timeout value
                            data = byte2_hex(received_data)
                            number = time.time() - delta_time
                            number = f"{number:24.4f}"
                            #length = len(bytearray.fromhex(str(received_data)))
                            #length = f"len = {length}"
                            length = len(received_data)
                            print(length)
                            data = number + ' : ' + data
                            self.uart_data.emit(data)
                            R_start_time = 0
                            received_data = bytearray()
            except serial.SerialException:
                self.uart_data.emit("Error: COM port disconnected.")
                self.disconnected.emit()
                break

if __name__ == "__main__":
    app = QApplication(sys.argv)
    uart_logger = UartLogger()
    uart_logger.show()
    sys.exit(app.exec())
