import sys
from unittest.mock import MagicMock, patch

# Patch 'tasks' and Firebase before importing any project code
sys.modules['tasks'] = MagicMock()
with patch('firebase_admin.initialize_app'), \
     patch('firebase_admin.get_app', return_value=MagicMock()), \
     patch('firebase_admin.firestore.client', return_value=MagicMock()):
    import os
    import logging
    import pytest
    from routes.padel_iq.analysis_manager import AnalysisManager

    def test_tensorflow_warning_suppression():
        """Test that TensorFlow warnings are properly suppressed."""
        # Get the current log level
        original_level = logging.getLogger('tensorflow').getEffectiveLevel()
        
        # Create an instance of AnalysisManager which should suppress warnings
        manager = AnalysisManager()
        
        # Verify that TensorFlow logging level is set to ERROR
        assert logging.getLogger('tensorflow').getEffectiveLevel() == logging.ERROR
        
        # Verify environment variable is set correctly
        assert os.environ.get('TF_CPP_MIN_LOG_LEVEL') == '2'
        
        # Restore original log level
        logging.getLogger('tensorflow').setLevel(original_level) 