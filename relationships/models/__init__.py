"""
Simply copy app_name.py relationship files into this file's directory
All relationships will automatically be imported.    
"""

import importlib
import pkgutil
import os

# Get the current package name
package_name = __name__

# Iterate through the modules in the current package
for _, module_name, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):
    if module_name != '__init__':
        # Import the module and add it to globals
        module = importlib.import_module(f".{module_name}", package_name)
        globals()[module_name] = module
