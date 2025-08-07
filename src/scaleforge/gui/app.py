
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
        )
        
        # Main content area
        content = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.8),
            padding=[dp(20), dp(10)],
            spacing=dp(15)
        )
            
        # TODO: Add actual model view components here
        content.add_widget(Label(
            text='Model Controls Will Appear Here',
            font_size=dp(16))
            
        # Footer with action buttons
        footer = BoxLayout(
            size_hint=(1, 0.1),
            spacing=dp(10),
            padding=[dp(20), 0])
        footer.add_widget(Button(
            text='Refresh',
            size_hint=(0.3, 1)))
        footer.add_widget(Button(
            text='Process',
            size_hint=(0.7, 1)))
            
        # Assemble full UI
        root.add_widget(header)
        root.add_widget(content)
        root.add_widget(footer)

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
