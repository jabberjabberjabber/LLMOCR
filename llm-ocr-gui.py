import sys
import os
import io
from typing import Optional, List
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
    QLineEdit, QLabel, QFileDialog, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from koboldapi import ImageProcessor
import requests

class LLMProcessor:
    def __init__(self, api_url, api_password, instruction):
        self.instruction = instruction
        self.max_length = 1024
        self.top_p = 1
        self.top_k = 0
        self.temperature = 0.1
        self.rep_pen = 1
        self.min_p = 0.1
        self.api_url = api_url
        self.api_password = api_password
        self.image_processor = ImageProcessor(max_dimension=896)
        self.system_instruction = "You are a helpful image capable model"
        
    def process_file(self, file_path):
        """Send frames to API for analysis"""
        image, output_path = self.image_processor.process_image(str(file_path))
        user_content = [{"type": "text", "text": self.instruction}]    
        if image:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image}"
                }
            })    
        try:
            messages = [
                {"role": "system", "content": self.system_instruction},
                {
                    "role": "user", 
                    "content": user_content 
                }
            ]
            
            payload = {
                #"model": "gpt-4-vision-preview", 
                "messages": messages,
                "max_tokens": self.max_length,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "rep_pen": self.rep_pen,
                "min_p": self.min_p
            }
            
            endpoint = f"{self.api_url}/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            if self.api_password:
                headers["Authorization"] = f"Bearer {self.api_password}"
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                
                if "message" in response_json["choices"][0]:
                    
                    return response_json["choices"][0]["message"]["content"], output_path
                
                else:
                    
                    return response_json["choices"][0].get("text", ""), output_path
            
            return None
            
        except Exception as e:
            raise Exception(f"Error in API call: {str(e)}")        
        
    def save_result(self, result: str, output_path: str) -> bool:
        """Save the processing result to a file"""
        txt_output_path = os.path.splitext(output_path)[0] + ".txt"
        try:
            with open(txt_output_path, "w", encoding="utf-8") as output_file:
                output_file.write(result)
            return True
        except Exception as e:
            print(f"Error saving to {txt_output_path}: {e}")
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
                    print(f"{result}")
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
            "*"
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
