"""Main window for FolderCrypto GUI application."""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QCheckBox,
    QMessageBox,
    QGroupBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

from app.services.encrypt_service import EncryptService
from app.services.decrypt_service import DecryptService
from app.core.exceptions import (
    FolderEncryptorError,
    InvalidPasswordError,
    DecryptionError,
    EncryptionError,
)
from app.utils.logger import setup_logging


logger = logging.getLogger(__name__)


class WorkerThread(QThread):
    """Worker thread for encryption/decryption operations."""

    progress = pyqtSignal(str, int, int)  # filename, current, total
    finished = pyqtSignal(bool, str)  # success, message
    log = pyqtSignal(str)  # log message

    def __init__(
        self,
        operation: str,
        input_path: str,
        output_path: str,
        password: str,
        use_argon2: bool = False,
    ):
        """Initialize worker thread.

        Args:
            operation: 'encrypt' or 'decrypt'
            input_path: Input folder path
            output_path: Output folder path
            password: Encryption/decryption password
            use_argon2: Whether to use Argon2 key derivation
        """
        super().__init__()
        self.operation = operation
        self.input_path = input_path
        self.output_path = output_path
        self.password = password
        self.use_argon2 = use_argon2

    def run(self):
        """Run the encryption/decryption operation."""
        try:
            def progress_callback(filename: str, current: int, total: int):
                self.progress.emit(filename, current, total)

            if self.operation == "encrypt":
                self.log.emit("Starting encryption...")
                service = EncryptService(use_argon2=self.use_argon2)
                service.encrypt_folder(
                    self.input_path,
                    self.output_path,
                    self.password,
                    progress_callback=progress_callback,
                )
                self.finished.emit(True, "Encryption completed successfully!")
            else:  # decrypt
                self.log.emit("Starting decryption...")
                service = DecryptService(use_argon2=self.use_argon2)
                service.decrypt_folder(
                    self.input_path,
                    self.output_path,
                    self.password,
                    progress_callback=progress_callback,
                )
                self.finished.emit(True, "Decryption completed successfully!")

        except InvalidPasswordError as e:
            self.finished.emit(False, f"Invalid password: {str(e)}")
        except (EncryptionError, DecryptionError) as e:
            self.finished.emit(False, f"Operation failed: {str(e)}")
        except FolderEncryptorError as e:
            self.finished.emit(False, f"Error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error in worker thread")
            self.finished.emit(False, f"Unexpected error: {str(e)}")


class CryptoTab(QWidget):
    """Base tab for encryption/decryption operations."""

    def __init__(self, operation: str):
        """Initialize crypto tab.

        Args:
            operation: 'encrypt' or 'decrypt'
        """
        super().__init__()
        self.operation = operation
        self.worker: Optional[WorkerThread] = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel(f"Folder {self.operation.capitalize()}")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Input folder group
        input_group = QGroupBox("Input Folder")
        input_layout = QHBoxLayout()
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText(
            "Select folder to encrypt..." if self.operation == "encrypt"
            else "Select encrypted folder..."
        )
        input_browse = QPushButton("Browse...")
        input_browse.clicked.connect(self.browse_input)
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(input_browse)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Output folder group
        output_group = QGroupBox("Output Folder")
        output_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText(
            "Select destination for encrypted files..." if self.operation == "encrypt"
            else "Select destination for decrypted files..."
        )
        output_browse = QPushButton("Browse...")
        output_browse.clicked.connect(self.browse_output)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_browse)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Password group
        password_group = QGroupBox("Password")
        password_layout = QVBoxLayout()
        
        password_row = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password...")
        self.show_password = QCheckBox("Show password")
        self.show_password.stateChanged.connect(self.toggle_password_visibility)
        password_row.addWidget(self.password_input)
        password_row.addWidget(self.show_password)
        password_layout.addLayout(password_row)

        # Argon2 option
        self.use_argon2 = QCheckBox("Use Argon2 key derivation (slower but more secure)")
        password_layout.addWidget(self.use_argon2)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)

        # Progress group
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        self.current_file_label = QLabel("Ready")
        self.current_file_label.setWordWrap(True)
        progress_layout.addWidget(self.current_file_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Log output
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Action button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.action_button = QPushButton(
            f"{self.operation.capitalize()} Folder"
        )
        self.action_button.clicked.connect(self.start_operation)
        self.action_button.setMinimumWidth(150)
        self.action_button.setMinimumHeight(40)
        button_layout.addWidget(self.action_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()
        self.setLayout(layout)

    def browse_input(self):
        """Browse for input folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Input Folder",
            str(Path.home()),
        )
        if folder:
            self.input_path.setText(folder)
            self.log_message(f"Input folder selected: {folder}")

    def browse_output(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(Path.home()),
        )
        if folder:
            self.output_path.setText(folder)
            self.log_message(f"Output folder selected: {folder}")

    def toggle_password_visibility(self, state):
        """Toggle password visibility."""
        if state == Qt.CheckState.Checked.value:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def log_message(self, message: str):
        """Add a message to the log output.

        Args:
            message: Message to log
        """
        self.log_output.append(message)
        # Auto-scroll to bottom
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_output.setTextCursor(cursor)

    def validate_inputs(self) -> bool:
        """Validate user inputs.

        Returns:
            True if inputs are valid, False otherwise
        """
        if not self.input_path.text():
            QMessageBox.warning(self, "Input Error", "Please select an input folder.")
            return False

        if not self.output_path.text():
            QMessageBox.warning(self, "Input Error", "Please select an output folder.")
            return False

        if not Path(self.input_path.text()).exists():
            QMessageBox.warning(self, "Input Error", "Input folder does not exist.")
            return False

        if not self.password_input.text():
            QMessageBox.warning(self, "Input Error", "Please enter a password.")
            return False

        if len(self.password_input.text()) < 8:
            reply = QMessageBox.question(
                self,
                "Weak Password",
                "Password is less than 8 characters. Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return False

        # Check if output folder exists and is not empty
        output_path = Path(self.output_path.text())
        if output_path.exists() and any(output_path.iterdir()):
            reply = QMessageBox.question(
                self,
                "Output Folder Exists",
                "Output folder exists and is not empty. Files may be overwritten. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return False

        return True

    def start_operation(self):
        """Start encryption/decryption operation."""
        if not self.validate_inputs():
            return

        # Disable UI during operation
        self.action_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_output.clear()
        self.current_file_label.setText("Initializing...")

        # Create and start worker thread
        self.worker = WorkerThread(
            operation=self.operation,
            input_path=self.input_path.text(),
            output_path=self.output_path.text(),
            password=self.password_input.text(),
            use_argon2=self.use_argon2.isChecked(),
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.operation_finished)
        self.worker.log.connect(self.log_message)
        self.worker.start()

    def update_progress(self, filename: str, current: int, total: int):
        """Update progress bar and status.

        Args:
            filename: Current file being processed
            current: Current file number
            total: Total number of files
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.current_file_label.setText(
                f"Processing ({current}/{total}): {Path(filename).name}"
            )
            self.log_message(f"[{current}/{total}] {filename}")

    def operation_finished(self, success: bool, message: str):
        """Handle operation completion.

        Args:
            success: Whether operation succeeded
            message: Result message
        """
        self.action_button.setEnabled(True)
        self.current_file_label.setText("Ready")

        if success:
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Success", message)
            self.log_message(f"✓ {message}")
        else:
            QMessageBox.critical(self, "Error", message)
            self.log_message(f"✗ {message}")


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("FolderCrypto - Secure Folder Encryption")
        self.setGeometry(100, 100, 800, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout()

        # Header
        header = QLabel("🔐 FolderCrypto")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Secure AES-256-GCM Folder Encryption & Decryption")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(CryptoTab("encrypt"), "Encrypt")
        tabs.addTab(CryptoTab("decrypt"), "Decrypt")
        layout.addWidget(tabs)

        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        footer = QLabel("Powered by AES-256-GCM encryption | PBKDF2/Argon2 key derivation")
        footer.setStyleSheet("color: gray; font-size: 10px;")
        footer_layout.addWidget(footer)
        footer_layout.addStretch()
        layout.addLayout(footer_layout)

        central_widget.setLayout(layout)

        # Apply styling
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #CCE5FF;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 2px solid #0078D4;
            }
            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 3px;
            }
            QTextEdit {
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                font-family: Consolas, monospace;
                font-size: 9pt;
            }
        """)


def main():
    """Run the GUI application."""
    # Setup logging
    setup_logging(verbose=True)

    # Create application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern cross-platform style

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
