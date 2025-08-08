from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
import subprocess

class ScaleForgeKivyApp(App):
    def build(self):
        layout = BoxLayout(orientation="vertical")
        self.filechooser = FileChooserIconView(filters=["*.jpg", "*.jpeg", "*.png", "*.webp"])
        layout.add_widget(self.filechooser)
        self.run_button = Button(text="Upscale selected images")
        self.run_button.bind(on_press=self.run_upscale)
        layout.add_widget(self.run_button)
        return layout

    def run_upscale(self, instance):
        for path in self.filechooser.selection:
            # Call the scaleforge CLI on the selected file. This assumes 'scaleforge' is on PATH via console_scripts.
            subprocess.run(["scaleforge", path], check=True)

if __name__ == "__main__":
    ScaleForgeKivyApp().run()
