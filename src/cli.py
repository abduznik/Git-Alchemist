import argparse
from . import __version__

def main():
    """Main function for the CLI."""
    parser = argparse.ArgumentParser(description="Git-Alchemist: AI-powered Git Operations", version=f"git-alchemist {__version__}")
    # ... rest of the code ...