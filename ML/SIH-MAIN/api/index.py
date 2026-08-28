import os
import sys

# Insert the parent directory (project root containing the 'app' folder) into sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
