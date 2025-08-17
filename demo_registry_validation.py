
#!/usr/bin/env python3
"""Demo script for registry validation functionality."""
import json
import tempfile
from pathlib import Path
from scaleforge.models.registry import validate_registry, load_registry_file

def demo_validation(data: dict) -> None:
    """Run and display validation results for given registry data."""
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w') as f:
        json.dump(data, f)
        f.flush()
        try:
            registry_data = load_registry_file(Path(f.name))
            is_valid, errors = validate_registry(registry_data)
            print("\n=== Validation Results ===")
            print(f"Valid: {is_valid}")
            if errors:
                print("Errors:")
                for error in errors:
                    print(f"- {error}")
            print(f"Models count: {len(registry_data.get('models', []))}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Valid case
    demo_validation({
        "models": [{
            "name": "valid_model",
            "url": "https://example.com/model.bin",
            "sha256": "a" * 64
        }]
    })

    # Invalid schema (missing name)
    demo_validation({
        "models": [{
            "url": "https://example.com/model.bin",
            "sha256": "a" * 64
        }]
    })

    # Duplicate names
    demo_validation({
        "models": [
            {"name": "dupe", "url": "u1", "sha256": "a" * 64},
            {"name": "dupe", "url": "u2", "sha256": "b" * 64}
        ]
    })
