import importlib
import sys

# def reload_modules():
#     for module_name in list(sys.modules.keys()):
#         if module_name.startswith('omwrapper'):
#             importlib.reload(sys.modules[module_name])

import sys

def reload_modules():
    for name in ['omwrapper']:
        loaded_package_modules = [key for key, value in sys.modules.items() if name in str(value)]
        for key in loaded_package_modules:
                print('unloading...', key)
                del sys.modules[key]