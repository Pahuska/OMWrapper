import importlib
import sys

def reload_modules():
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('omwrapper'):
            importlib.reload(sys.modules[module_name])

def unload_package(package_name):
    import sys

    to_delete = [
        m for m in sys.modules
        if m == package_name or m.startswith(package_name + ".")
    ]

    for m in to_delete:
        print("unloading : ", m)
        del sys.modules[m]