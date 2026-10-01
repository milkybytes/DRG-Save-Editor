import os
import sys

# main.py runs as a script with its own folder on the path, so its sibling modules
# (gvas, campaigns, ...) are imported by bare name. Do the same for the tests.
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "src", "main", "python")
)
