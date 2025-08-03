
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (StringProperty, NumericProperty, ObjectProperty)
from kivy.clock import Clock
from pathlib import Path

from kivy.properties import BooleanProperty

class JobCard(BoxLayout):
    """Widget displaying live job status with controls."""
    job_id = StringProperty('')
    input_path = ObjectProperty(None)
    output_path = ObjectProperty(None)
    status = StringProperty('queued')
    progress = NumericProperty(0)
    message = StringProperty('')
    paused = BooleanProperty(False)
    queue = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._status_poller = None
        
        # Create retries label
        from kivy.uix.label import Label
        self.retries_label = Label(
            text='',
            size_hint=(None, None),
            size=(100, 20),
            color=(0.6, 0.6, 0.6, 1),
            font_size='10sp'
        )
        self.add_widget(self.retries_label)
        
        # Initialize tooltips after widgets are created
        Clock.schedule_once(self._setup_tooltips)
        
        self.bind(
            input_path=lambda i, v: setattr(self.ids.input_label, 'text', v.name if v else ""),
            output_path=lambda i, v: setattr(self.ids.output_label, 'text', v.name if v else ""),
            paused=self._update_button_states
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._status_poller = None
        self.enable_tooltips = True  # Tooltip toggle flag
        self._hover_timeout = None  # For debounce tracking

    def _show_tooltip(self, button, *args):
        """Show tooltip after debounce delay if enabled."""
        if self.enable_tooltips and hasattr(button, 'tooltip'):
            button.tooltip.opacity = 1

    def _setup_tooltips(self, *args):
        """Add tooltips to control buttons with hover behavior."""
        from kivy.core.window import Window
        from kivy.uix.tooltip import Tooltip
        from kivy.metrics import dp
        from kivy.clock import Clock
        
        if not hasattr(self, 'ids') or not self.enable_tooltips:
            return
            
        # Pause/Resume button tooltip
        self.ids.pause_btn.tooltip = Tooltip(
            text='Pause job execution' if not self.paused else 'Resume job execution',
            background=(0.2, 0.2, 0.2, 0.9),
            size_hint=(None, None),
            size=(dp(200), dp(50)),  # Constrained max width
            text_size=(dp(190), None),  # Text wrapping
            halign='left',
            valign='middle'
        )
        self.ids.pause_btn.tooltip.opacity = 0
        Window.add_widget(self.ids.pause_btn.tooltip)
        self.ids.pause_btn.tooltip.canvas.before.opacity = 1  # Ensure proper layering
        
        # Cancel button tooltip
        self.ids.cancel_btn.tooltip = Tooltip(
            text='Cancel this job',
            background=(0.2, 0.2, 0.2, 0.9),
            size_hint=(None, None),
            size=(dp(200), dp(50)),
            text_size=(dp(190), None),
            halign='left',
            valign='middle'
        )
        self.ids.cancel_btn.tooltip.opacity = 0
        Window.add_widget(self.ids.cancel_btn.tooltip)
        self.ids.cancel_btn.tooltip.canvas.before.opacity = 1
        
        # Delete button tooltip
        self.ids.delete_btn.tooltip = Tooltip(
            text='Delete this job (cannot be undone)',
            background=(0.2, 0.2, 0.2, 0.9),
            size_hint=(None, None),
            size=(dp(200), dp(50)),
            text_size=(dp(190), None),
            halign='left',
            valign='middle'
        )
        self.ids.delete_btn.tooltip.opacity = 0
        Window.add_widget(self.ids.delete_btn.tooltip)
        self.ids.delete_btn.tooltip.canvas.before.opacity = 1
        
        # Bind hover events
        self.ids.pause_btn.bind(
            on_enter=lambda b: (
                self._hover_timeout and self._hover_timeout.cancel(),
                Clock.schedule_once(lambda dt: setattr(b.tooltip, 'opacity', 1), 0.15)
                if self.enable_tooltips else None
            ),
            on_leave=lambda b: (
                self._hover_timeout and self._hover_timeout.cancel(),
                setattr(b.tooltip, 'opacity', 0)
            )
        )
        self.ids.cancel_btn.bind(
            on_enter=lambda b: (self._hover_timeout and self._hover_timeout.cancel(), Clock.schedule_once(lambda dt: setattr(b.tooltip, 'opacity', 1), 0.15) if self.enable_tooltips else None),
            on_leave=lambda b: (self._hover_timeout and self._hover_timeout.cancel(), setattr(b.tooltip, 'opacity', 0))
        )
        self.ids.delete_btn.bind(
            on_enter=lambda b: (self._hover_timeout and self._hover_timeout.cancel(), Clock.schedule_once(lambda dt: setattr(b.tooltip, 'opacity', 1), 0.15) if self.enable_tooltips else None),
            on_leave=lambda b: (self._hover_timeout and self._hover_timeout.cancel(), setattr(b.tooltip, 'opacity', 0))
        )

    def _update_button_states(self, *args):
        """Update button states and tooltips."""
        if not hasattr(self, 'ids'):
            return
            
        # Update pause/resume tooltip text
        if hasattr(self.ids.pause_btn, 'tooltip'):
            self.ids.pause_btn.tooltip.text = 'Resume job execution' if self.paused else 'Pause job execution'
            
        # Rest of button state logic...
        self.ids.pause_btn.text = 'Resume' if self.paused else 'Pause'
        self.ids.pause_btn.disabled = not (
            (self.status == 'running' and not self.paused) or 
            (self.status == 'paused' and self.paused)
        )
        self.ids.cancel_btn.disabled = self.status not in ('queued', 'running', 'paused')
        self.ids.delete_btn.disabled = self.status in ('running', 'paused')

    def on_delete(self, *args):
        """Clean up tooltips before deletion."""
        if hasattr(self, 'ids'):
            for btn in [self.ids.pause_btn, self.ids.cancel_btn, self.ids.delete_btn]:
                if hasattr(btn, 'tooltip'):
                    btn.tooltip.opacity = 0
                    btn.tooltip.parent.remove_widget(btn.tooltip)
        super().on_delete(*args)

        self.ids.pause_btn.background_color = (0.9, 0.9, 0.9, 1) if self.ids.pause_btn.disabled else (0.8, 0.9, 1, 1)
        self.ids.cancel_btn.background_color = (0.9, 0.9, 0.9, 1) if self.ids.cancel_btn.disabled else (1, 0.8, 0.8, 1)

    def on_pause_resume(self):
        """Handle pause/resume button press."""
        if self.paused:
            self.queue.resume_job(self.job_id)
        else:
            self.queue.pause_job(self.job_id)
        self.paused = not self.paused
        self._update_button_states()

    def on_cancel(self):
        """Handle cancel button press."""
        self.queue.cancel_job(self.job_id)
        self._update_button_states()

    def on_delete(self):
        """Handle delete button press with confirmation."""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        
        def confirm_delete(instance):
            if self.queue.delete_job(self.job_id):
                if self.parent:
                    self.parent.remove_widget(self)
            popup.dismiss()
            
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text="Are you sure you want to delete this job?\nThis cannot be undone."))
        
        btn_layout = BoxLayout(spacing=5)
        btn_layout.add_widget(Button(text='Cancel', on_press=lambda x: popup.dismiss()))
        btn_layout.add_widget(Button(text='Delete', on_press=confirm_delete))
        content.add_widget(btn_layout)
        
        popup = Popup(title='Confirm Delete',
                     size_hint=(0.6, 0.3),
                     content=content)
        popup.open()

    def start_polling(self, queue, interval=0.5):
        """Start polling job status updates."""
        self._status_poller = Clock.schedule_interval(
            lambda dt: self._update_status(queue), interval
        )

    def _update_status(self, queue):
        """Update widget with latest job status."""
        try:
            status = queue.get_job_status(self.job_id)
            if not status:
                return
                
            self.status = status.status
            self.progress = status.progress
            self.message = status.message
            
            # Safely update retries counter display
            try:
                if hasattr(self, 'retries_label'):
                    retries = getattr(status, 'retries_left', 0)
                    if retries > 0:
                        self.retries_label.text = f"Retries left: {retries}"
                        self.retries_label.opacity = 1
                    else:
                        self.retries_label.text = ''
                        self.retries_label.opacity = 0
            except Exception as e:
                print(f"Error updating retry counter: {e}")
            
            if status.status in ('complete', 'failed'):
                self.stop_polling()
                
        except Exception as e:
            print(f"Status update error: {e}")
            self.stop_polling()

    def stop_polling(self):
        """Stop status polling safely."""
        if getattr(self, '_status_poller', None):
            try:
                self._status_poller.cancel()
            except:
                pass  # Poller already cancelled or invalid
            finally:
                self._status_poller = None
