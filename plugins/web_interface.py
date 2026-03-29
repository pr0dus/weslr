
# web_interface.py - Plugin for Weslr
# Template for new plugins

# Required metadata
PLUGIN_INFO = {
    "name": "web_interface",
    "version": "0.1.0",
    "description": "Web-based chat interface",
    "author": "Human",
    "enabled": True,
}

# Plugin functions go here
def initialize():
    print(f"web_interface plugin initialized")

def process_input(input_data):
    return input_data

def get_capabilities():
    return ["basic_processing"]

# Optional integration hook
def integrate_with_circleforge():
    return {"capabilities": get_capabilities()}

# Run on module load
if __name__ == "__main__":
    initialize()
