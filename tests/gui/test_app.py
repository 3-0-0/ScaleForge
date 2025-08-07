

import pytest
from unittest.mock import MagicMock, patch
from scaleforge.gui.app import ScaleForgeApp

@pytest.fixture
def mock_kivy():
    with patch.dict('sys.modules', {
        'kivy': MagicMock(),
        'kivy.app': MagicMock(),
        'watchdog.observers': MagicMock()
    }):
        yield

def test_app_initialization(mock_kivy):
    """Test GUI starts in headless mode without errors"""
    app = ScaleForgeApp(headless=True)
    app.build()  # Should not raise exceptions
    assert app.model_watcher is None  # In headless mode

def test_refresh_models(mock_kivy):
    """Test model refresh functionality"""
    app = ScaleForgeApp(headless=True)
    app.model_manager = MagicMock()
    app.refresh_models()
    app.model_manager.load_all.assert_called_once()

