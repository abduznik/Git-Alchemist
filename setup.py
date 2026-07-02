from setuptools import setup

def get_version():
    """Get the version from the __init__.py file."""
    with open('src/__init__.py', 'r') as f:
        for line in f:
            if line.startswith('__version__ ='):
                return line.split('=')[1].strip().strip("'")
    return "Unknown"

setup(
    name='git-alchemist',
    version=get_version(),
    # ... rest of the setup code ...
)