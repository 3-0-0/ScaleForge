from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.properties import ObjectProperty

class JobPanel(BoxLayout):
    job_queue = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.update_panel()
    
    def update_panel(self):
        self.clear_widgets()
        for job in self.job_queue.get_active_jobs():
            self.add_widget(JobItem(job))

class JobItem(BoxLayout):
    def __init__(self, job, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text=job.src_path))
        self.add_widget(ProgressBar(value=job.progress))
