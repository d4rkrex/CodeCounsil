#!/usr/bin/env python3
import json
import shutil

from core.evidence.collector import TOOL_ALLOWLIST


def main() -> None:
    detections = {}
    for name, command in TOOL_ALLOWLIST.items():
        binary = shutil.which(command[0])
        detections[name] = {
            "detected": binary is not None,
            "binary": binary,
            "command": command,
        }
    print(json.dumps(detections, indent=2))


if __name__ == "__main__":
    main()
