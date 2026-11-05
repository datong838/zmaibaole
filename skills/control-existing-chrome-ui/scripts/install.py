#!/usr/bin/env python3
"""Install only the skill instructions. Does not touch Chrome or permissions."""
import argparse
from pathlib import Path
import shutil

source=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dest',type=Path,default=Path.home()/'.codex/skills/control-existing-chrome-ui')
args=parser.parse_args()
dest=args.dest.expanduser().resolve()
if dest.exists(): parser.error('Destination exists; refusing to overwrite')
if dest==source or source in dest.parents: parser.error('Destination must be outside source')
shutil.copytree(source,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
print(str(dest))
print('Skill files installed. No Chrome extension, permissions, debug port or local HTTP service was installed.')
