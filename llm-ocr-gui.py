import sys
import base64
import requests
import os
import io
from typing import Optional, List
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
    QLineEdit, QLabel, QFileDialog, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class LLMProcessor:
    def __init__(self, api_url: str, api_password: str, instruction: str):
        self.api_url = api_url
        self.instruction = instruction
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_password}",
        }

    def encode_file_to_base64(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Error encoding file {file_path}: {e}")
            return None

    def send_image_to_llm(self, base64_image: str) -> Optional[str]:
        prompt = f"<|im_start|>user\n{self.instruction}<|im_end|>\n<|im_start|>assistant\n"
        payload = {
            "prompt": prompt,
            "max_context": 4096,
            "max_length": 1024,
            "images": [base64_image],
            "top_p": 1,
            "top_k": 0,
            "temp": 0,
            "rep_pen": 1.05,
            "min_p": 0.02,
        }
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/generate", 
                json=payload, 
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()["results"][0].get("text")
        except Exception as e:
            print(f"Error in LLM request: {e}")
            return None

    def process_file(self, file_path: str) -> tuple[Optional[str], str]:
        """Process an image file and return (result, output_path)"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ('.png', '.jpg', '.jpeg'):
            result = self.encode_file_to_base64(file_path)
            if result:
                result = self.send_image_to_llm(result)
            output_path = os.path.splitext(file_path)[0] + ".txt"
            return result, output_path
        else:
            return None, ""

    def save_result(self, result: str, output_path: str) -> bool:
        """Save the processing result to a file"""
        try:
            with open(output_path, "w", encoding="utf-8") as output_file:
                output_file.write(result)
            return True
        except Exception as e:
            print(f"Error saving to {output_path}: {e}")
            return False

class ProcessingThread(QThread):
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, processor: LLMProcessor, files: List[str]):
        super().__init__()
        self.processor = processor
        self.files = files
        
    def run(self):
        try:
            for i, file_path in enumerate(self.files):
                result, output_path = self.processor.process_file(file_path)
                if result:
                    self.processor.save_result(result, output_path)
                self.progress.emit(i + 1, len(self.files))
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM Image Processor")
        self.setMinimumWidth(600)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # API URL
        layout.addWidget(QLabel("API URL:"))
        self.api_url = QLineEdit("http://localhost:5001")
        layout.addWidget(self.api_url)
        
        # API Password
        layout.addWidget(QLabel("API Password:"))
        self.api_password = QLineEdit()
        self.api_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_password)
        
        # Instruction
        layout.addWidget(QLabel("Instruction:"))
        self.instruction = QTextEdit()
        self.instruction.setPlaceholderText("Enter instruction for the LLM...")
        self.instruction.setMaximumHeight(100)
        self.instruction.setText("Repeat verbatim all text on the image.")
        layout.addWidget(self.instruction)
        
        # File selection
        self.file_button = QPushButton("Select Images")
        self.file_button.clicked.connect(self.select_files)
        layout.addWidget(self.file_button)
        
        # Selected files display
        self.files_label = QLabel("No files selected")
        layout.addWidget(self.files_label)
        
        # Progress bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        # Process button
        self.process_button = QPushButton("Process Images")
        self.process_button.clicked.connect(self.process_files)
        self.process_button.setEnabled(False)
        layout.addWidget(self.process_button)
        
        self.selected_files = []
        
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg)"
        )
        if files:
            self.selected_files = files
            self.files_label.setText(f"Selected {len(files)} images")
            self.process_button.setEnabled(True)
    
    def process_files(self):
        if not self.selected_files:
            return
            
        self.process_button.setEnabled(False)
        self.file_button.setEnabled(False)
        
        processor = LLMProcessor(
            self.api_url.text(),
            self.api_password.text(),
            self.instruction.toPlainText()
        )
        
        self.thread = ProcessingThread(processor, self.selected_files)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.processing_finished)
        self.thread.error.connect(self.processing_error)
        self.thread.start()
    
    def update_progress(self, current, total):
        self.progress.setValue(int((current / total) * 100))
    
    def processing_finished(self):
        self.process_button.setEnabled(True)
        self.file_button.setEnabled(True)
        self.files_label.setText("Processing completed")
        self.progress.setValue(0)
    
    def processing_error(self, error_msg):
        self.process_button.setEnabled(True)
        self.file_button.setEnabled(True)
        self.files_label.setText(f"Error: {error_msg}")
        self.progress.setValue(0)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()