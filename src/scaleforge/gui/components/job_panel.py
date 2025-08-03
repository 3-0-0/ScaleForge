

"""Job monitoring panel component."""
from kivy.uix.recycleview import RecycleView
from kivy.properties import ObjectProperty

class JobMonitor(RecycleView):
    """RecycleView-based job monitoring panel."""
    
    job_queue = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.viewclass = 'Label'
        self.data = [{'text': 'Job monitoring will appear here'}]
        
    def update_jobs(self):
        """Update the view with current job states."""
        if self.job_queue:
            self.data = [{'text': str(job)} for job in self.job_queue.jobs]

