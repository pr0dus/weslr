# export_functionality.py - Plugin for Weslr
# Export functionality for external tools

PLUGIN_INFO = {
    "name": "export_functionality",
    "version": "0.1.0",
    "description": "Export functionality for external tools (JSON, CSV, etc.)",
    "author": "Weslr",
    "enabled": True,
}


def initialize():
    """Initialize export functionality."""
    print("export_functionality plugin initialized")
    return {"status": "initialized"}


def export_to_json(data: dict, filename: str = None) -> dict:
    """Export data to JSON format."""
    import json
    content = json.dumps(data, indent=2)
    
    if filename:
        with open(filename, 'w') as f:
            f.write(content)
        return {
            "status": "success",
            "format": "json",
            "filename": filename,
            "content_length": len(content),
        }
    else:
        return {
            "status": "success",
            "format": "json",
            "content": content,
            "content_length": len(content),
        }


def export_to_csv(data: list, filename: str = None) -> dict:
    """Export data to CSV format."""
    import csv
    import io
    
    if not data:
        return {"status": "error", "message": "No data to export"}
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    content = output.getvalue()
    
    if filename:
        with open(filename, 'w') as f:
            f.write(content)
        return {
            "status": "success",
            "format": "csv",
            "filename": filename,
            "content_length": len(content),
        }
    else:
        return {
            "status": "success",
            "format": "csv",
            "content": content,
            "content_length": len(content),
        }


def export_to_markdown(data: dict, filename: str = None) -> dict:
    """Export data to Markdown format."""
    
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"## {key}")
            for sub_key, sub_value in value.items():
                lines.append(f"- {sub_key}: {sub_value}")
        else:
            lines.append(f"- {key}: {value}")
    
    content = '\n'.join(lines)
    
    if filename:
        with open(filename, 'w') as f:
            f.write(content)
        return {
            "status": "success",
            "format": "markdown",
            "filename": filename,
            "content_length": len(content),
        }
    else:
        return {
            "status": "success",
            "format": "markdown",
            "content": content,
            "content_length": len(content),
        }


def get_capabilities() -> list:
    """Return available capabilities."""
    return [
        "export_to_json",
        "export_to_csv",
        "export_to_markdown",
        "export_to_file",
    ]


# Optional integration hook
def integrate_with_circleforge():
    """Integrate this plugin with Weslr."""
    return {
        "capabilities": get_capabilities(),
        "integration_status": "ready",
    }


# Run on module load
if __name__ == "__main__":
    initialize()
