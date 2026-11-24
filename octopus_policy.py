"""P0 fail-closed candidate path policy; not a sandbox."""
import re
def authorize(repository, branch, paths):
    if repository != "js775315672-spec/Octopus-Free-24H":
        raise ValueError("repository denied")
    if not re.fullmatch(r"dev/[a-z0-9][a-z0-9-]*", branch):
        raise ValueError("branch denied")
    if not paths:
        raise ValueError("empty change")
    for path in paths:
        if not isinstance(path, str) or not re.fullmatch(r"candidates/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_-]+)*\.py", path):
            raise ValueError("path denied")
    return True
