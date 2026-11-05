"""One pinned Python runtime for executable complaint tools; never installs packages."""
from pathlib import Path
import os,sys

def ensure_runtime(project=None):
    project=Path(project).resolve() if project else Path(__file__).resolve().parents[3]
    environment=project/'skills/daily-comment-stats/.venv'
    executable=environment/'bin/python'
    if Path(sys.prefix).resolve()==environment.resolve():return
    if not executable.is_file() or not os.access(executable,os.X_OK):raise RuntimeError('complaint-runtime-missing:'+str(executable))
    os.execv(str(executable),[str(executable),str(Path(sys.argv[0]).resolve()),*sys.argv[1:]])
    raise RuntimeError('complaint-runtime-reexec-returned')
