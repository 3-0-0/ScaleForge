

"""Resolution preset editor dialog component."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import ListProperty
from scaleforge.utils.presets_io import load_presets, save_presets

class ResolutionEditorPopup(Popup):
    """Popup window for editing resolution presets."""
    
    def __init__(self, on_save_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.title = "Edit Resolution Presets"
        self.size_hint = (0.8, 0.8)
        self.on_save_callback = on_save_callback
        
        layout = BoxLayout(orientation='vertical')
        self.presets_list = BoxLayout(orientation='vertical')
        self._refresh_presets_list()
        
        # Add controls
        controls = BoxLayout(size_hint_y=0.2)
        self.width_input = TextInput(hint_text="Width", input_filter='int')
        self.height_input = TextInput(hint_text="Height", input_filter='int')
        add_btn = Button(text="Add", on_press=self._add_preset)
        controls.add_widget(self.width_input)
        controls.add_widget(self.height_input)
        controls.add_widget(add_btn)
        
        layout.add_widget(Label(text="Current Presets:"))
        layout.add_widget(self.presets_list)
        layout.add_widget(controls)
        layout.add_widget(Button(text="Save", on_press=self._save_presets))
        
        self.content = layout
    
    def _refresh_presets_list(self):
        """Reload and display current presets."""
        self.presets_list.clear_widgets()
        for preset in load_presets():
            row = BoxLayout(size_hint_y=None, height=40)
            row.add_widget(Label(text=preset["label"]))
            row.add_widget(Button(
                text="Remove", 
                on_press=lambda btn, p=preset: self._remove_preset(p)
            ))
            self.presets_list.add_widget(row)
    
    def _add_preset(self, instance):
        """Add new resolution preset."""
        try:
            width = int(self.width_input.text)
            height = int(self.height_input.text)
            if width <= 0 or height <= 0:
                raise ValueError("Dimensions must be positive")
                
            presets = load_presets()
            label = f"{width}x{height}"
            if any(p["label"] == label for p in presets):
                raise ValueError("Preset already exists")
                
            presets.append({"label": label, "width": width, "height": height})
            save_presets(presets)
            self._refresh_presets_list()
            
            # Clear inputs
            self.width_input.text = ""
            self.height_input.text = ""
            
        except ValueError as e:
            print(f"Invalid preset: {e}")
    
    def _remove_preset(self, preset):
        """Remove a resolution preset."""
        presets = [p for p in load_presets() if p["label"] != preset["label"]]
        save_presets(presets)
        self._refresh_presets_list()
    
    def _save_presets(self, instance):
        """Handle save button press."""
        self.dismiss()
        if self.on_save_callback:
            self.on_save_callback()

