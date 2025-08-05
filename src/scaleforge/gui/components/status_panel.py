

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel

class StatusPanel(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        self.label_jobs = QLabel("Pending: 0")
        self.label_progress = QLabel("Progress: 0/0")
        self.label_gpu = QLabel("GPU: Ready")
        
        self.layout.addWidget(self.label_jobs)
        self.layout.addWidget(self.label_progress)
        self.layout.addWidget(self.label_gpu)

    def update_counts(self, pending_jobs: int):
        self.label_jobs.setText(f"Pending: {pending_jobs}")

    def update_progress(self, completed: int, total: int):
        self.label_progress.setText(f"Progress: {completed}/{total}")
        self.label_gpu.setStyleSheet("")  # Clear error styling

    def show_error(self, message):
        """Display error message with visual emphasis"""
        self.label_gpu.setText(f"Error: {message}")
        self.label_gpu.setStyleSheet("color: red; font-weight: bold;")
        self.label_progress.setText("Failed")

