from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ModelRefreshHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"DEBUG: File system event detected - {event.event_type} on {event.src_path}")
        if 'scaleforge.yaml' in event.src_path:
            print("CONFIG MODIFIED - RELOAD TRIGGERED")
            App.get_running_app().refresh_models()
        else:
            print(f"Ignoring non-config file change: {event.src_path}")

class ScaleForgeApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from kivy.utils import platform
        self.platform = platform
        print(f"Running on: {platform}")

    def populate_model_dropdown(self):
        """Populate model dropdown with available options"""
        models = ["realesrgan-x4plus", "realesrgan-x4plus-anime", "realesrgan-x2plus"]
        self.model_dropdown.clear_widgets()
        for model in models:
            btn = Button(text=model, size_hint_y=None, height=dp(40))
            btn.bind(on_release=lambda btn: self.select_model(btn.text))
            self.model_dropdown.add_widget(btn)

    def select_model(self, model):
        """Handle model selection"""
        self.model_select.text = model
        self.state["current_model"] = model
        self.model_dropdown.dismiss()
        self.log(f"[UI] Model selected: {model}")

    def handle_model_dropdown(self, instance):
        """Handle model dropdown opening with logging"""
        self.log("[UI] Model dropdown opened")
        self.populate_model_dropdown()
        self.model_dropdown.open(instance)

    def populate_resolution_dropdown(self):
        """Populate resolution dropdown with available options"""
        resolutions = ["720p", "1080p", "4K", "8K"]
        self.res_dropdown.clear_widgets()
        for res in resolutions:
            btn = Button(text=res, size_hint_y=None, height=dp(40))
            btn.bind(on_release=lambda btn: self.select_resolution(btn.text))
            self.res_dropdown.add_widget(btn)

    def select_resolution(self, resolution):
        """Handle resolution selection"""
        self.res_select.text = resolution
        self.state["current_resolution"] = resolution
        self.res_dropdown.dismiss()
        self.log(f"[UI] Resolution selected: {resolution}")

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

    def setup_file_watcher(self):
        """Initialize file system watcher for config changes"""
        print("DEBUG: Initializing file watcher")
        try:
            self.observer = Observer()
            handler = ModelRefreshHandler()
            print(f"DEBUG: Watching path: {os.path.abspath('.')}")
            self.observer.schedule(handler, path='.', recursive=False)
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
