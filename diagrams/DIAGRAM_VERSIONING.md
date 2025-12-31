Diagram Versioning Policy

Purpose
- Ensure diagram artifacts are versioned and immutable once published.
- New edits must produce a new file (not overwrite) with a semantic version suffix.

Filename convention
- Use the pattern: <name>_v<MAJOR>.<MINOR>.<PATCH>.mmd
  - Example: role_architecture_v1.2.0.mmd

Embedding version metadata
- Each versioned diagram SHOULD include a header at the top with metadata:
  - %% Version: 1.2.0
  - %% Source: <original-filename>
  - Optionally: %% Author, %% Date

Creating a new version (recommended workflow)
1. Copy the latest file to a new filename with a bumped semantic version (e.g., v1.2.1).
2. Update the header metadata inside the new file (Version, Date, Change summary).
3. Validate the Mermaid syntax (tools or mermaid-diagram-validator).
4. Commit the new file to the repository (do NOT modify or delete prior versions unless intentionally archiving).

Quick helper script (Python) - safe copy and bump patch version

```python
# diagrams/bump_diagram_version.py
import re
from pathlib import Path

def bump_patch_version(filename: Path) -> Path:
    m = re.search(r"_v(\d+)\.(\d+)\.(\d+)\.mmd$", filename.name)
    if not m:
        raise SystemExit("Filename must end with _vMAJOR.MINOR.PATCH.mmd")
    major, minor, patch = map(int, m.groups())
    new_patch = patch + 1
    new_name = filename.with_name(f"{filename.stem[:-len(m.group(0))+1]}_v{major}.{minor}.{new_patch}.mmd")
    return new_name

# Usage example (manual):
# from pathlib import Path
# src = Path('role_architecture_v1.2.0.mmd')
# dst = bump_patch_version(src)
# dst.write_text(src.read_text().replace('Version: 1.2.0','Version: 1.2.1'))
```

Notes
- Prefer bumping patch for minor edits, minor for feature additions, and major for breaking layout or schema changes.
- Keep the original file(s) read-only in practice to preserve provenance.

Contact
- If you want, I can create a small CLI script to automate safe version bumps and header updates. Let me know and I'll add it to the repo.
