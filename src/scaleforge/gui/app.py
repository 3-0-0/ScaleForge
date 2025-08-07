from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.metrics import dp
import os
import subprocess
import json
from queue import Queue
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ModelRefreshHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Completely ignore log/tmp files and directories
        if any(event.src_path.endswith(ext) for ext in ['.log', '.tmp']) or event.is_directory:
            return None
            
        print(f"DEBUG: Processing file event - {event.event_type} on {event.src_path}")
        if 'scaleforge.yaml' in event.src_path:
            print("CONFIG MODIFIED - RELOAD TRIGGERED")
            App.get_running_app().refresh_models()
        else:
            print(f"Ignoring non-config file change: {event.src_path}")

class ScaleForgeApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.job_queue = Queue()
        Thread(target=self.job_worker, daemon=True).start()
        from kivy.utils import platform
        self.platform = platform
        print(f"Running on: {platform}")
        
        # Initialize UI components
        self.log_panel = None
        self.model_select = None
        self.res_select = None
        self.model_dropdown = None
        self.res_dropdown = None
        
        # Initialize state and presets
        self.DEFAULT_STATE = {
            "current_model": None,
            "current_resolution": None,
            "input_path": None,
            "output_path": None,
            "resolutions": []
        }
        
        self.resolution_presets = {
            "720p": [1280, 720],
            "1080p": [1920, 1080],
            "4K": [3840, 2160],
            "8K": [7680, 4320]
        }
        
        try:
            state_path = os.path.expanduser("~/.scaleforge_state.json")
            with open(state_path) as f:
                self.state = json.load(f)
            self.log("[STATE] Loaded saved state")
        except Exception as e:
            self.state = self.DEFAULT_STATE.copy()
            self.log(f"[STATE] Using default state ({str(e)})")
            
        self.available_models = []
        self.log_panel = None  # Will be set in setup_ui
        self.scan_models()

    def save_state(self):
        """Persist current state to disk"""
        try:
            state_path = os.path.expanduser("~/.scaleforge_state.json")
            with open(state_path, 'w') as f:
                json.dump(self.state, f)
            self.log("[STATE] Saved current state")
        except Exception as e:
            self.log(f"[STATE ERROR] Failed to save state: {str(e)}")

    def log(self, message):
        """Add timestamped message to log panel"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        if self.log_panel:
            self.log_panel.text += log_entry
        print(log_entry.strip())

    def scan_models(self):
        """Scan models directory for available models"""
        models_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
        if os.path.exists(models_dir):
            self.available_models = [
                os.path.splitext(f)[0] 
                for f in os.listdir(models_dir) 
                if f.endswith('.pth')
            ]
            for model in self.available_models:
                self.log(f"[CORE] Found model: {model}")
        else:
            self.log("[WARNING] Models directory not found")

    def populate_model_dropdown(self):
        """Populate model dropdown with available options"""
        self.model_dropdown.clear_widgets()
        for model in self.available_models:
            btn = Button(text=model, size_hint_y=None, height=dp(40))
            btn.bind(on_release=lambda btn: self.select_model(btn.text))
            self.model_dropdown.add_widget(btn)

    def select_model(self, model):
        """Handle model selection"""
        self.model_select.text = model
        self.state["current_model"] = model
        self.model_dropdown.dismiss()
        self.log(f"[UI] Model selected: {model}")
        self.save_state()

    def handle_model_dropdown(self, instance):
        """Handle model dropdown opening with logging"""
        self.log("[UI] Model dropdown opened")
        self.populate_model_dropdown()
        self.model_dropdown.open(instance)

    def populate_resolution_dropdown(self):
        """Populate resolution dropdown with available presets"""
        resolutions = list(self.resolution_presets.keys())
        self.res_dropdown.clear_widgets()
        for res in resolutions:
            btn = Button(text=res, size_hint_y=None, height=dp(40))
            btn.bind(on_release=lambda btn: self.select_resolution(btn.text))
            self.res_dropdown.add_widget(btn)

    def select_resolution(self, resolution):
        """Handle resolution selection"""
        self.res_select.text = resolution
        self.state["current_resolution"] = self.resolution_presets[resolution]
        self.log(f"[UI] Resolution selected: {resolution} ({self.state['current_resolution'][0]}×{self.state['current_resolution'][1]})")
        self.save_state()
        self.res_dropdown.dismiss()


    def handle_resolution_dropdown(self, instance):
        """Handle resolution dropdown opening with logging"""
        self.log("[UI] Resolution dropdown opened")
        self.populate_resolution_dropdown()
        self.res_dropdown.open(instance)

    def handle_add_resolution(self, instance):
        """Handle resolution add button click"""
        self.state["resolutions"].append("dummy-res")
        self.log("[UI] Resolution added")
        self.log(f"Current resolutions: {self.state['resolutions']}")

    def handle_remove_resolution(self, instance):
        """Handle resolution remove button click"""
        if self.state["resolutions"]:
            self.state["resolutions"].pop()
            self.log("[UI] Resolution removed")
            self.log(f"Current resolutions: {self.state['resolutions']}")

    def job_worker(self):
        """Process jobs from the queue"""
        while True:
            job = self.job_queue.get()
            self.log(f"[QUEUE] Starting job (queue size: {self.job_queue.qsize()})")
            self._execute_job(**job)
            self.job_queue.task_done()

    def _execute_job(self, model, resolution, input_path, output_path):
        """Internal method to actually run a job"""
        self.log("[JOB] Starting upscale job...")
        self.log(f"[JOB] Using model: {model}")
        self.log(f"[JOB] Target resolution: {resolution}")
        result = subprocess.run(
            ["python", "inference_realesrgan.py",
             "-i", input_path,
             "-o", output_path,
             "-n", model,
             "--res", str(resolution[0])],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            self.log("[JOB] Completed successfully")
        else:
            self.log(f"[JOB] Failed with code {result.returncode}")
            if result.stderr:
                self.log(f"[ERROR] {result.stderr}")

    def run_job(self, instance):
        """Handle job execution when Start button is pressed"""
        try:
            if not self.state["current_model"]:
                self.log("[ERROR] No model selected")
                return
            if not self.state["current_resolution"]:
                self.log("[ERROR] No resolution selected")
                return
            self.job_queue.put({
                'model': self.state['current_model'],
                'resolution': self.state['current_resolution'],
                'input_path': self.state['input_path'],
                'output_path': self.state['output_path']
            })
            self.log(f"[QUEUE] Job enqueued (queue size: {self.job_queue.qsize()})")





            
        except Exception as e:
            self.log(f"[EXCEPTION] {str(e)}")

    def setup_file_watcher(self):
        """Initialize file system watcher for config changes"""
        print("DEBUG: Initializing file watcher")
        try:
            self.observer = Observer()
            handler = ModelRefreshHandler()
            print(f"DEBUG: Watching path: {os.path.abspath('.')}")
            
            # Create custom event filter to ignore log files
            from watchdog.observers.api import DEFAULT_OBSERVER_TIMEOUT, BaseObserver
            class FilteredObserver(BaseObserver):
                def schedule(self, event_handler, path=None, recursive=False):
                    if any(path.endswith(ext) for ext in ['.log', '.tmp']):
                        return
                    super().schedule(event_handler, path, recursive)
            
            from watchdog.observers.inotify import InotifyEmitter
            self.observer = FilteredObserver(
                emitter_class=InotifyEmitter,
                timeout=DEFAULT_OBSERVER_TIMEOUT
            )
            self.observer.schedule(handler)
            self.observer.start()
            print("DEBUG: File watcher started successfully")
        except Exception as e:
            print(f"ERROR in file watcher: {str(e)}")
            raise

    def build(self):
        # Main container with consistent padding
        root = BoxLayout(
            orientation='vertical',
            padding=[20, 20, 20, 20],
            spacing=15
        )
        
        # Setup core UI components
        self.setup_file_watcher()
        self.setup_ui(root)
        
        return root
        
    def setup_ui(self, root):
        """Initialize all UI components with consistent styling"""
        from kivy.metrics import dp
        from kivy.uix.button import Button
        from kivy.uix.label import Label
        
        # Initialize application state
        self.state = {
            "current_model": None,
            "current_resolution": None,
            "resolutions": []
        }

        # Create and configure Start button
        start_btn = Button(
            text='Start Processing',
            size_hint=(1, 0.1),
            background_color=(0.2, 0.7, 0.3, 1)
        )
        start_btn.bind(on_press=self.run_job)
        root.add_widget(start_btn)

        # Create log panel
        from kivy.uix.scrollview import ScrollView
        from kivy.core.window import Window
        scroll = ScrollView(size_hint=(1, 0.4))
        self.log_panel = Label(
            text='System Log:\n',
            size_hint_y=None,
            halign='left',
            valign='top',
            text_size=(Window.width - 40, None)
        )
        self.log_panel.bind(size=self.log_panel.setter('text_size'))
        scroll.add_widget(self.log_panel)
        root.add_widget(scroll)

        # Header section
        header = BoxLayout(
            size_hint=(1, 0.1),
            padding=[dp(10), dp(5)],
            spacing=dp(15)
        )
        header.add_widget(Label(
            text='ScaleForge',
            font_size=dp(24),
            halign='left'
        ))
        
        # [Rest of original file content...]

if __name__ == '__main__':
    ScaleForgeApp().run()
