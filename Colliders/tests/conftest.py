import sys
import os
import pytest

# Ensure Colliders directory is in sys.path
colliders_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if colliders_dir not in sys.path:
    sys.path.insert(0, colliders_dir)


@pytest.fixture
def app():
    """Create Flask application fixture for testing."""
    import api
    api.app.config['TESTING'] = True
    return api.app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()
