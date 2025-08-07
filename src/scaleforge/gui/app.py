
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
        # TODO: Implement responsive UI components here
        # Use dp units for sizing that scales across devices
        # Example:
        # self.model_view = ModelView(size_hint=(1, 0.8))
        # root.add_widget(self.model_view)
        return BoxLayout()

    def setup_file_watcher(self):
        handler = ModelRefreshHandler()
        self.observer = Observer()
        self.observer.schedule(handler, path='.', recursive=False)
        self.observer.start()

    def refresh_models(self):
        print("DEBUG: Model refresh triggered")
        # Actual refresh logic would go here

    def on_stop(self):
        self.observer.stop()
        self.observer.join()

def run(debug=False):
    if debug:
        print("Starting in debug mode")
    ScaleForgeApp().run()
