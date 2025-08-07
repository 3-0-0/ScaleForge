


# Test implementation with required permissions
class App:
    _running_app = None
    
    @classmethod
    def get_running_app(cls):
        return cls._running_app

class BoxLayout:
    pass

class ScaleForgeApp:
    def __init__(self, headless=False):
        self.headless = headless
        self.model_watcher = None
        self._model_manager = None
        
    @property
    def model_manager(self):
        return self._model_manager
        
    @model_manager.setter
    def model_manager(self, value):
        self._model_manager = value
        
    def build(self):
        return BoxLayout()
        
    def refresh_models(self):
        if self.model_manager:
            self.model_manager.load_all()


