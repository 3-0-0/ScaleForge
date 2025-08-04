from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from scaleforge.config import load_config

class ResolutionPresetManager(GridLayout):
    def __init__(self, on_preset_select, **kwargs):
        super().__init__(**kwargs)
        self.cols = 3
        self.on_preset_select = on_preset_select
        self._load_presets()
    
    def _load_presets(self):
        config = load_config()
        for preset in config.resolution_presets:
            btn = Button(text=preset['name'])
            btn.bind(on_press=lambda _, p=preset: self.on_preset_select(p))
            self.add_widget(btn)
