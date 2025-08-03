from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.properties import ListProperty

class FileDropTarget(BoxLayout):
    file_paths = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_dropfile=self._handle_drop)
    
    def _handle_drop(self, window, file_path):
        self.file_paths.append(file_path.decode('utf-8'))
