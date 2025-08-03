from kivy.app import App
from .drag_drop import FileDropTarget
from .preset_manager import ResolutionPresetManager
from .event_bridge import JobQueueObserver
from scaleforge.pipeline.queue import JobQueue

class ScaleForgeApp(App):
    def build(self):
        self.job_queue = JobQueue()
        self.observer = JobQueueObserver(
            self.job_queue, 
            self.root.job_panel.update_panel
        )
        return MainUI(job_queue=self.job_queue)
    
    def on_stop(self):
        self.observer.stop()

class MainUI(BoxLayout):
    def __init__(self, job_queue, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        # Add file drop target
        self.drop_target = FileDropTarget(size_hint_y=0.1)
        self.drop_target.bind(file_paths=self._handle_files)
        self.add_widget(self.drop_target)
        
        # Add resolution presets
        self.preset_manager = ResolutionPresetManager(
            self._on_preset_select,
            size_hint_y=0.1
        )
        self.add_widget(self.preset_manager)
        
        # Add job panel
        self.job_panel = JobPanel(job_queue=job_queue)
        self.add_widget(self.job_panel)
    
    def _handle_files(self, instance, value):
        self.job_queue.enqueue(value)
    
    def _on_preset_select(self, preset):
        print(f"Selected preset: {preset['name']}")
