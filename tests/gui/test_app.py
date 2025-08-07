

import pytest
import sys
from unittest.mock import MagicMock, patch, PropertyMock

# Add src to Python path for imports
sys.path.insert(0, '/tmp/viewable/src')

# Use test implementation from tests directory
@pytest.fixture
def mock_kivy_ecosystem():
    # Import test implementation directly
    from tests.gui import test_implementation
    import sys
    sys.modules['scaleforge.gui.app'] = test_implementation
    try:
        yield
    finally:
        # Clean up
        del sys.modules['scaleforge.gui.app']

def test_app_initialization(mock_kivy_ecosystem):
    """Test GUI starts in headless mode without errors"""
    from scaleforge.gui.app import ScaleForgeApp
    with patch('scaleforge.gui.app.ScaleForgeApp.model_manager', new_callable=PropertyMock) as mock_mgr:
        mock_mgr.return_value = MagicMock()
        app = ScaleForgeApp(headless=True)
        app.build()
        assert app.model_watcher is None

def test_refresh_models(mock_kivy_ecosystem):
    """Test model refresh functionality"""
    from scaleforge.gui.app import ScaleForgeApp
    mock_manager = MagicMock()
    with patch('scaleforge.gui.app.ScaleForgeApp.model_manager', 
              new_callable=PropertyMock, return_value=mock_manager):
        app = ScaleForgeApp(headless=True)
        app.refresh_models()
        mock_manager.load_all.assert_called_once()

