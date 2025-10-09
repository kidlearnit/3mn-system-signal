import os
import sys
import pytest


@pytest.fixture(scope="session")
def flask_app():
    # Ensure project root on path so we can import init
    this_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(this_dir, '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from init import app as flask_app_instance
        return flask_app_instance
    except ModuleNotFoundError:
        # Try package-style import
        sys.path.insert(0, os.path.abspath(os.path.join(project_root, '..')))
        from backend.init import app as flask_app_instance
        return flask_app_instance


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()


