#!/usr/bin/env python3
"""Copy a clean, key-free skill; never install an extension or launch Chrome silently."""
import argparse
from pathlib import Path
import shutil

src=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--dest',type=Path,default=Path.home()/'.codex/skills/chrome-dom-export')
a=p.parse_args()
dest=a.dest.expanduser().resolve()
if dest.exists():
    p.error('Destination exists; refusing to replace reviewed code or local keys')
if src==dest or src in dest.parents:
    p.error('Destination cannot be inside source')
shutil.copytree(src,dest,ignore=shutil.ignore_patterns('.local','config.js','__pycache__','*.pyc','.DS_Store'))
print(str(dest))
print('Next: python3 "'+str(dest/'scripts/bridge.py')+'" init')
