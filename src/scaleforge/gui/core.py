
"""Core Kivy GUI components for ScaleForge."""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import (ObjectProperty, StringProperty, 
                           BooleanProperty, ListProperty)
from kivy.clock import Clock
from kivy.core.window import Window
from pathlib import Path
from scaleforge.gui.components.job_panel import JobMonitor
from scaleforge.jobs.queue import JobQueue

class ResolutionPopup(Popup):
    """Popup for custom resolution input."""
    width_input = ObjectProperty(None)
    height_input = ObjectProperty(None)
    
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = "Add Custom Resolution"
        self.size_hint = (0.6, 0.4)
        self.callback = callback
        
    def confirm_resolution(self):
        """Handle resolution confirmation."""
        try:
            width = int(self.width_input.text)
            height = int(self.height_input.text)
            self.callback(f"{width}x{height}")
            self.dismiss()
        except ValueError:
            pass

class MainUI(BoxLayout):
    """Main application UI layout."""
    job_monitor = ObjectProperty(None)
    selected_resolution = StringProperty("1920x1080")
    dry_run = BooleanProperty(False)
    dropped_files = ListProperty([])
    cli_preview = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.job_queue = JobQueue()
        Window.bind(on_dropfile=self._on_dropfile)
        self._setup_controls()
        self._setup_job_monitor()
        self._setup_dummy_jobs()
        Clock.schedule_interval(self._update_jobs, 2.0)
        Clock.schedule_once(self._update_cli_preview)
    
    def _setup_controls(self):
        """Add resolution controls and CLI preview."""
        # Resolution buttons
        resolutions = BoxLayout(size_hint_y=0.1)
        for res in ["1920x1080", "3840x2160", "7680x4320"]:
            btn = Button(text=res)
            btn.bind(on_press=lambda x, r=res: self._set_resolution(r))
            resolutions.add_widget(btn)
        
        # Custom resolution button
        custom_btn = Button(text="+ Custom", size_hint_y=0.1)
        custom_btn.bind(on_press=self._show_custom_res_popup)
        resolutions.add_widget(custom_btn)
        self.add_widget(resolutions)
        
        # Dry run toggle
        self.dry_run_toggle = ToggleButton(
            text="Dry Run", 
            size_hint_y=0.05,
            group="dry_run"
        )
        self.dry_run_toggle.bind(active=self._on_dry_run_toggle)
        self.add_widget(self.dry_run_toggle)
        
        # CLI preview
        self.cli_label = TextInput(
            text=self.cli_preview,
            size_hint_y=0.1,
            readonly=True
        )
        self.add_widget(self.cli_label)
    
    def _on_dropfile(self, window, file_path):
        """Handle file drop events."""
        path = Path(file_path.decode('utf-8'))
        self.dropped_files.append(path)
        print(f"File dropped: {path}")  # Simulate queueing
        self._update_cli_preview()
    
    def _set_resolution(self, resolution):
        """Set selected resolution."""
        self.selected_resolution = resolution
        self._update_cli_preview()
    
    def _show_custom_res_popup(self, instance):
        """Show custom resolution popup."""
        popup = ResolutionPopup(self._set_resolution)
        popup.open()
    
    def _on_dry_run_toggle(self, instance, value):
        """Handle dry run toggle."""
        self.dry_run = value
        self._update_cli_preview()
    
    def _update_cli_preview(self, *args):
        """Update CLI command preview."""
        res = self.selected_resolution
        dry_run = "--dry-run" if self.dry_run else ""
        paths = " ".join(f'"{p}"' for p in self.dropped_files[-3:])  # Show last 3
        if len(self.dropped_files) > 3:
            paths += f" (+{len(self.dropped_files)-3} more)"
            
        self.cli_preview = (
            f"scaleforge run {paths or '<input>'} "
            f"--res {res} --output <output> {dry_run}"
        )
        self.cli_label.text = self.cli_preview
    
    def _setup_job_monitor(self):
        """Initialize and add job monitor widget."""
        self.job_monitor = JobMonitor(job_queue=self.job_queue)
        self.add_widget(self.job_monitor)
    
    def _setup_dummy_jobs(self):
        """Add sample jobs for UI testing."""
        if not self.job_queue.jobs:
            from scaleforge.jobs.base import JobStatus
            self.job_queue.add_job(
                id="job1", 
                src_path="sample1.png", 
                status=JobStatus.PENDING
            )
            self.job_queue.add_job(
                id="job2", 
                src_path="sample2.png", 
                status=JobStatus.COMPLETED
            )
            self.job_queue.add_job(
                id="job3", 
                src_path="sample3.png", 
                status=JobStatus.FAILED
            )
    
    def _update_jobs(self, dt):
        """Periodic job status update."""
        if self.job_monitor:
            self.job_monitor.update_jobs()

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
