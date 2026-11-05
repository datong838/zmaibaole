#!/usr/bin/env python3
"""Run only formal skills/packages tests, each file in a fresh interpreter.
--list does not import tests. work/runtime/dist and virtual environments are never roots.
"""
import argparse,json,os,re,subprocess,sys
from pathlib import Path
EXCLUDED={'work','runtime','dist','venv','.venv','env','.git','node_modules','__pycache__'}
def formal_tests(project):
 project=Path(project).resolve();files=[]
 for category in ('skills','packages'):
  base=project/category
  if not base.is_dir():continue
  for owner in sorted(base.iterdir()):
   root=owner/'tests'
   if not root.is_dir():continue
   if root.resolve()!=root or owner.is_symlink() or root.is_symlink():raise ValueError('formal-test-root-symlink')
   for path in sorted(root.rglob('test_*.py')):
    relative=path.relative_to(root)
    if any(part in EXCLUDED for part in relative.parts):continue
    if path.resolve()!=path or any(x.is_symlink() for x in (path,*path.parents)):raise ValueError('formal-test-file-symlink')
    if not re.fullmatch(r'test_[A-Za-z0-9_]+\.py',path.name):raise ValueError('formal-test-filename')
    files.append(path)
 return files
def main(argv=None,*,project=None,run=subprocess.run):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--list',action='store_true');parser.add_argument('--suite',help='one formal skills/NAME/tests or packages/NAME/tests');args=parser.parse_args(argv)
 project=Path(project or Path(__file__).resolve().parent).resolve();files=formal_tests(project)
 if args.suite:
  suite=Path(args.suite)
  if suite.is_absolute() or len(suite.parts)!=3 or suite.parts[0] not in ('skills','packages') or suite.parts[2]!='tests' or suite.parts[1] in ('.','..'):raise ValueError('only-formal-test-suite-accepted')
  files=[p for p in files if p.is_relative_to(project/suite)]
 if not files:raise ValueError('no-formal-tests-selected')
 if args.list:print(json.dumps({'kind':'formal-test-file-list-v1','count':len(files),'files':[str(p.relative_to(project)) for p in files]},indent=2));return 0
 results=[]
 for file in files:
  # No parent-process discovery/import: all monkeypatch/module state dies with this child.
  command=[sys.executable,'-B','-m','unittest','discover','-s',str(file.parent),'-p',file.name]
  completed=run(command,cwd=project);results.append({'file':str(file.relative_to(project)),'returncode':completed.returncode})
 print(json.dumps({'kind':'formal-tests-isolated-results-v1','results':results,'successful':all(r['returncode']==0 for r in results)},indent=2));return 0 if all(r['returncode']==0 for r in results) else 1
if __name__=='__main__':
 try:raise SystemExit(main())
 except ValueError as error:print(json.dumps({'ok':False,'error':str(error)}),file=sys.stderr);raise SystemExit(2)
