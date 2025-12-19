# Project Constraints

## Critical: Path Handling
- The workspace root is `/home/leeo/Documents/code/thermalright-lcd-control/`.
- **NEVER** prepend the absolute path to a path that already starts with `/home/leeo/`.
- Use relative paths (starting with `./`) for all tool arguments.
- If you see a path like `/home/leeo/.../home/leeo/...`, it is an error. Strip the first segment and use only the second absolute path or convert it to relative.
