
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton
from scaleforge.backend.selector import get_backend
from scaleforge.pipeline.queue import JobQueue

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.backend = get_backend()
        self.job_queue = JobQueue(config.database_path, self.backend)
        
        self.setWindowTitle("ScaleForge")
        self.setMinimumSize(800, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        self.layout = QVBoxLayout()
        central.setLayout(self.layout)

        # Components
        from scaleforge.gui.components.file_input import FileInput
        from scaleforge.gui.components.status_panel import StatusPanel
        
        self.file_input = FileInput(self)
        self.status_panel = StatusPanel(self)
        
        self.layout.addWidget(self.file_input)
        self.layout.addWidget(self.status_panel)
        
        # Control buttons
        self.btn_start = QPushButton("Start Processing")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_start.clicked.connect(self.on_start)
        self.btn_cancel.clicked.connect(self.on_cancel)
        
        self.layout.addWidget(self.btn_start)
        self.layout.addWidget(self.btn_cancel)

    def on_start(self):
        """Start processing jobs"""
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.job_queue.process_async(
            progress_callback=lambda c,t: self.status_panel.update_progress(c,t),
            completion_callback=self.on_complete,
            error_callback=self.on_error
        )
        self.refresh_job_queue()

    def on_cancel(self):
        """Cancel current processing"""
        self.job_queue.cancel_all()
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.refresh_job_queue()

    def on_complete(self):
        """Handle job completion"""
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.status_panel.update_progress(0, 0)  # Reset progress
        self.refresh_job_queue()

    def on_error(self, error):
        """Handle processing errors"""
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.status_panel.show_error(str(error))
        self.refresh_job_queue()

    def refresh_job_queue(self):
        """Update UI with current queue status"""
        with self.job_queue.conn:
            pending = len(self.job_queue.pending())
            self.status_panel.update_counts(pending)
