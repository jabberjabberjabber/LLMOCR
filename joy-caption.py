import sys
import os
import io
import time
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
    QLineEdit, QLabel, QFileDialog, QProgressBar, QTextEdit, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from koboldapi import KoboldAPICore, ImageProcessor

class ClipboardHandler:
    """Copies to clipboard across all platforms"""
    
    def __init__(self, app: QApplication):
        self._app = app
        self._clipboard = self._app.clipboard()

    def copy_text(self, text: str) -> bool:
        try:
            self._clipboard.setText(text)
            return self._clipboard.text() == text
        except Exception as e:
            print(f"Error copying to clipboard: {str(e)}")
            return False

class LLMProcessor:
    def __init__(self, api_url, system_instruction, instruction):
        self.instruction = instruction
        self.system_instruction = system_instruction
        self.core = KoboldAPICore(api_url=api_url)
        self.image_processor = ImageProcessor(max_dimension=384)
        
    def process_file(self, file_path: str) -> tuple[Optional[str], str]:
        """Process an image file and return (result, output_path)"""
        start_time = time.time()
        encoded_image, output_path = self.image_processor.process_image(str(file_path))
        result = self.core.wrap_and_generate(
            instruction=self.instruction, 
            system_instruction=self.system_instruction,
            model_name="llama3",
            images=[encoded_image],
            max_length=256,
            top_p=0.95,
            top_k=0,
            temp=0.6,
            rep_pen=1.1,
            min_p=0.1
        )
        total_time = time.time() - start_time
        print(f"{os.path.basename(file_path)} processed in {total_time:.2f} seconds:\n------------\n{result}\n------------\n")
        return result, output_path
        
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
    result_ready = pyqtSignal(str)  # Clipboard signal
    
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
                    self.result_ready.emit(result)
                self.progress.emit(i + 1, len(self.files))
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.system_instruction = "You are a helpful image captioner."
        self.default_instruction = "Describe the image in detail. Be specific."       
        self.setWindowTitle("LLM Image Processor")
        self.setMinimumWidth(600)
        self.clipboard_handler = ClipboardHandler(QApplication.instance())
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        layout.addWidget(QLabel("API URL:"))
        self.api_url = QLineEdit("http://localhost:5001")
        layout.addWidget(self.api_url)
        
        layout.addWidget(QLabel("Select Instruction:"))
        self.instruction_combo = QComboBox()
        self.instruction_combo.addItems([
            "Provide a brief description of the image.",
            "Write a descriptive caption for this image in a formal tone within 250 words.",
            "Write a long descriptive caption for this image in a formal tone.",
            "Write a descriptive caption for this image in a formal tone.",
            "Write a stable diffusion prompt for this image.",
            "Write a stable diffusion prompt for this image within 250 words.",
            "Write a MidJourney prompt for this image.",
            "Write a list of Booru tags for this image.",
            "Write a list of Booru-like tags for this image.",
            "Analyze this image like an art critic would.",
            "Describe the main objects and their relationships in the image."
        ])
        layout.addWidget(self.instruction_combo)
        
        layout.addWidget(QLabel("Instruction:"))
        self.instruction = QLineEdit(self.default_instruction)        
        layout.addWidget(self.instruction)
        self.instruction_combo.currentTextChanged.connect(self.instruction.setText)
        
        self.file_button = QPushButton("Select Images")
        self.file_button.clicked.connect(self.select_files)
        layout.addWidget(self.file_button)
        
        self.files_label = QLabel("No files selected")
        layout.addWidget(self.files_label)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        self.process_button = QPushButton("Process Images")
        self.process_button.clicked.connect(self.process_files)
        self.process_button.setEnabled(False)
        layout.addWidget(self.process_button)
        
        self.result_label = QLabel("")
        layout.addWidget(self.result_label)
        
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
            self.system_instruction,
            self.instruction.text()
        )
        
        self.thread = ProcessingThread(processor, self.selected_files)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.processing_finished)
        self.thread.error.connect(self.processing_error)
        self.thread.result_ready.connect(self.handle_result)
        self.thread.start()
    
    def handle_result(self, result: str):
        """Handle new result by copying to clipboard and updating UI"""
        if self.clipboard_handler.copy_text(result):
            self.result_label.setText("Result copied to clipboard!")
        else:
            self.result_label.setText("Failed to copy result to clipboard")
    
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
        self.result_label.setText("")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()