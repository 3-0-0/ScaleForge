
"""Core Kivy GUI components for ScaleForge."""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from scaleforge.jobs.base import JobStatus
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import (ObjectProperty, StringProperty, 
                           BooleanProperty, ListProperty)
from kivy.clock import Clock
from kivy.core.window import Window
from pathlib import Path
from scaleforge.gui.components.job_panel import JobMonitor
from scaleforge.jobs.queue import JobQueue
from scaleforge.utils.settings_io import load_settings, save_settings

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
        self.settings = load_settings()
        self.output_dir = Path(self.settings.get("output_path", "output"))
        self.selected_resolution = self.settings.get("resolution", "1920x1080")
        self.dry_run = self.settings.get("dry_run", False)
        self.job_queue = JobQueue(output_dir=self.output_dir)
        Window.bind(on_dropfile=self._on_dropfile)
        self._setup_controls()
        self._setup_job_monitor()
        Clock.schedule_interval(self._update_jobs, 2.0)
        Clock.schedule_once(self._update_cli_preview)

    def _on_dropfile(self, window, file_path):
        """Handle file/folder drop events by creating jobs."""
        path = Path(file_path.decode('utf-8'))
        supported_ext = ('.png', '.jpg', '.jpeg')
        
        if path.is_dir():
            # Recursively scan folder for image files
            for ext in supported_ext:
                for img_path in path.rglob(f'*{ext}'):
                    self._create_job(img_path)
        elif path.suffix.lower() in supported_ext:
            self._create_job(path)
            
    def _create_job(self, path):
        """Create job from path and update UI."""
        self.dropped_files.append(path)
        job_id = f"job_{len(self.job_queue.jobs)+1}"
        self.job_queue.add_job(
            id=job_id,
            src_path=path,
            resolution=self.selected_resolution,
            dry_run=self.dry_run
        )
        self._update_cli_preview()
    
    def _setup_controls(self):
        """Add all control elements and connect settings persistence."""
        # Connect output path field
        self.ids.output_path.bind(text=self._on_output_path_change)
        
        # Connect resolution selector
        self.ids.resolution_selector.bind(text=self._on_resolution_change)
        
        # Connect dry run toggle
        self.ids.dry_run_toggle.bind(active=self._on_dry_run_toggle)
        
        # Add edit resolutions button
        self.ids.edit_resolutions_btn.bind(on_press=self._open_resolution_editor)
        
        controls = BoxLayout(orientation='vertical', size_hint_y=0.3)
        
        # File selection controls
        file_controls = BoxLayout(size_hint_y=0.15)
        self.add_images_btn = Button(text="Add Image(s)")
        self.add_images_btn.bind(on_press=self._show_file_chooser)
        file_controls.add_widget(self.add_images_btn)
        
        self.output_folder_btn = Button(text="Set Output Folder")
        self.output_folder_btn.bind(on_press=self._show_folder_chooser)
        file_controls.add_widget(self.output_folder_btn)
        controls.add_widget(file_controls)

        # Resolution controls
        resolutions = BoxLayout(size_hint_y=0.15)
        for res in ["1920x1080", "3840x2160", "7680x4320"]:
            btn = Button(text=res)
            btn.bind(on_press=lambda x, r=res: self._set_resolution(r))
            resolutions.add_widget(btn)
        
        custom_btn = Button(text="+ Custom", size_hint_y=0.15)
        custom_btn.bind(on_press=self._show_custom_res_popup)
        resolutions.add_widget(custom_btn)
        controls.add_widget(resolutions)
        
        # Execution controls
        exec_controls = BoxLayout(size_hint_y=0.1)
        self.dry_run_toggle = ToggleButton(
            text="Dry Run",
            group="dry_run",
            state='down' if self.dry_run else 'normal'
        )
        self.dry_run_toggle.bind(state=lambda i, v: self._on_dry_run_toggle(v == 'down'))
        exec_controls.add_widget(self.dry_run_toggle)
        
        self.start_btn = Button(text="Start Processing")
        self.start_btn.bind(on_press=self._start_processing)
        exec_controls.add_widget(self.start_btn)
        controls.add_widget(exec_controls)
        
        # CLI preview
        self.cli_label = TextInput(
            text=self.cli_preview,
            size_hint_y=0.1,
            readonly=True
        )
        controls.add_widget(self.cli_label)
        
        self.add_widget(controls)
    


    def _show_file_chooser(self, instance):
        """Show file chooser popup for image selection."""
        from kivy.uix.filechooser import FileChooserListView
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        
        content = BoxLayout(orientation='vertical')
        chooser = FileChooserListView(filters=['*.png', '*.jpg', '*.jpeg'])
        content.add_widget(chooser)
        
        btn_layout = BoxLayout(size_hint_y=0.2)
        btn_cancel = Button(text='Cancel')
        btn_select = Button(text='Select')
        btn_layout.add_widget(btn_cancel)
        btn_layout.add_widget(btn_select)
        content.add_widget(btn_layout)
        
        popup = Popup(title='Select Images', content=content, size_hint=(0.9, 0.9))
        
        def add_jobs(instance):
            for f in chooser.selection:
                path = Path(f)
                job_id = f"job_{len(self.job_queue.jobs)+1}"
                self.job_queue.add_job(
                    id=job_id,
                    src_path=path,
                    dst_path=self.output_dir / path.name,
                    resolution=self.selected_resolution,
                    dry_run=self.dry_run
                )
            popup.dismiss()
            self._update_cli_preview()
            self._update_jobs(0)
        
        btn_select.bind(on_press=add_jobs)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()




    def _show_folder_chooser(self, instance):
        """Show folder chooser popup for output directory."""
        from kivy.uix.filechooser import FileChooserListView
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        
        content = BoxLayout(orientation='vertical')
        chooser = FileChooserListView(dirselect=True)
        content.add_widget(chooser)
        
        btn_layout = BoxLayout(size_hint_y=0.2)
        btn_cancel = Button(text='Cancel')
        btn_select = Button(text='Select')
        btn_layout.add_widget(btn_cancel)
        btn_layout.add_widget(btn_select)
        content.add_widget(btn_layout)
        
        popup = Popup(title='Select Output Folder', content=content, size_hint=(0.9, 0.9))
        
        def select_folder(instance):
            if chooser.selection:
                self.output_dir = Path(chooser.selection[0])
                self.output_dir.mkdir(exist_ok=True)
                popup.dismiss()
        
        btn_select.bind(on_press=select_folder)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()




    def _start_processing(self, instance):
        """Start processing all pending jobs in background threads."""
        import threading
        from scaleforge.jobs.base import JobStatus
        
        self.start_btn.disabled = True
        pending_jobs = [j for j in self.job_queue.jobs if j.status == JobStatus.PENDING]
        
        if not pending_jobs:
            print("No pending jobs to process")
            self.start_btn.disabled = False
            return
            
        print(f"Starting {len(pending_jobs)} jobs...")
        
        def job_complete_callback(job):
            self._update_jobs(0)
            if all(j.status != JobStatus.PENDING for j in self.job_queue.jobs):
                self.start_btn.disabled = False
                print("All jobs completed")
        
        for job in pending_jobs:
            def process_job(job):
                job.process(self.output_dir)
                Clock.schedule_once(lambda dt: job_complete_callback(job))
            
            threading.Thread(target=process_job, args=(job,), daemon=True).start()






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

    def _on_output_path_change(self, instance, value):
        """Handle output directory changes."""
        self.output_dir = Path(value)
        self.settings["output_path"] = value
        save_settings(self.settings)
        self._update_cli_preview()

    def _on_resolution_change(self, instance, value):
        """Handle resolution selection changes."""
        self.selected_resolution = value
        self.settings["resolution"] = value
        save_settings(self.settings)
        self._update_cli_preview()

    def _on_dry_run_toggle(self, instance, value):
        """Handle dry run toggle changes."""
        self.dry_run = value
        self.settings["dry_run"] = value
        save_settings(self.settings)
        self._update_cli_preview()

    def _open_resolution_editor(self, instance):
        """Open resolution preset editor dialog."""
        from scaleforge.gui.components.resolution_editor import ResolutionEditorPopup
        from scaleforge.utils.presets_io import load_presets
        
        def refresh_resolutions():
            """Callback to refresh resolution selector after edits."""
            resolution_selector = self.ids.resolution_selector
            current = resolution_selector.text
            resolution_selector.values = [
                p["label"] for p in load_presets()
            ]
            resolution_selector.text = current if current in resolution_selector.values else ""

        popup = ResolutionEditorPopup(on_save_callback=refresh_resolutions)
        popup.open()

class ScaleForgeApp(App):
    """Main Kivy application class."""
    
    def build(self):
        """Initialize and return the root widget."""
        self.title = 'ScaleForge'
        self.root = MainUI()
        
        # Apply window size from settings
        if hasattr(self.root, 'settings'):
            window_size = self.root.settings.get('window_size', [800, 600])
            Window.size = (window_size[0], window_size[1])
            
        return self.root

    def on_stop(self):
        """Save settings when app closes."""
        if hasattr(self, 'root') and hasattr(self.root, 'settings'):
            # Save current window size
            self.root.settings['window_size'] = list(Window.size)
            save_settings(self.root.settings)
        return super().on_stop()
