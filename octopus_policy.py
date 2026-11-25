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

def authorize_workspace(root, repository, branch, paths):
    """Preflight for trusted, exclusively owned workspace; not race-safe sandbox."""
    from pathlib import Path
    import stat
    paths = tuple(paths)
    authorize(repository, branch, paths)
    root = Path(root).resolve(strict=True)
    for path in paths:
        current = root
        for index, part in enumerate(path.split("/")):
            current = current / part
            try:
                info = current.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(info.st_mode):
                raise ValueError("symlink denied")
            if index == len(path.split("/")) - 1:
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise ValueError("nonregular or hardlinked file denied")
            elif not stat.S_ISDIR(info.st_mode):
                raise ValueError("non-directory parent denied")
    return True
