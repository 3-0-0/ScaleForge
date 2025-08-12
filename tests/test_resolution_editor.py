

"""Non-GUI tests for resolution preset editor functionality."""
import unittest
from unittest.mock import patch, Mock
from pathlib import Path
from scaleforge.utils.presets_io import load_presets, save_presets

class TestResolutionEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup test presets file
        cls.test_file = Path(".scaleforge/test_presets.json")
        cls.test_file.parent.mkdir(exist_ok=True)
        save_presets([
            {"label": "512x512", "width": 512, "height": 512},
            {"label": "1024x768", "width": 1024, "height": 768}
        ])

    def test_preset_operations(self):
        """Test core preset operations without GUI."""
        # Test loading
        presets = load_presets()
        self.assertEqual(len(presets), 2)
        
        # Test adding
        new_preset = {"label": "800x600", "width": 800, "height": 600}
        save_presets(presets + [new_preset])
        updated = load_presets()
        self.assertEqual(len(updated), 3)
        self.assertIn(new_preset, updated)
        
        # Test removing
        save_presets([p for p in updated if p["label"] != "512x512"])
        filtered = load_presets()
        self.assertEqual(len(filtered), 2)
        self.assertNotIn({"label": "512x512"}, filtered)

    @patch('scaleforge.utils.presets_io.load_presets')
    def test_refresh_logic(self, mock_load):
        """Test resolution refresh callback logic."""
        from scaleforge.gui.components.resolution_editor import ResolutionEditorPopup
        
        mock_load.return_value = [
            {"label": "640x480", "width": 640, "height": 480}
        ]
        
        popup = ResolutionEditorPopup()
        callback = popup.on_save_callback
        mock_selector = Mock()
        mock_selector.text = "640x480"
        
        with patch.object(popup, 'ids', {'resolution_selector': mock_selector}):
            callback()
            mock_selector.values = ['640x480']
            self.assertEqual(mock_selector.text, "640x480")

    @classmethod 
    def tearDownClass(cls):
        # Cleanup test file
        cls.test_file.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()

