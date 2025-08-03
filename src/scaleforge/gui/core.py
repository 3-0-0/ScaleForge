
"""Core Kivy GUI components for ScaleForge."""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty

class MainUI(BoxLayout):
    """Main application UI layout."""
    job_monitor = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

class ScaleForgeApp(App):
    """Main Kivy application class."""
    
    def build(self):
        """Initialize and return the root widget."""
        self.title = 'ScaleForge'
        return MainUI()

    def on_stop(self):
        """Cleanup when application stops."""
        # Add any necessary cleanup here
        return super().on_stop()
