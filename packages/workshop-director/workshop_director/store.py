"""SQLite queue transactions plus fsynced immutable process receipts."""
import json,sqlite3
from pathlib import Path
from .common import *
class Store:
    def __init__(self,root):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.root/'queue.sqlite3',timeout=30);self.db.row_factory=sqlite3.Row
        self.db.executescript('''PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
        CREATE TABLE IF NOT EXISTS plans(id TEXT PRIMARY KEY,payload TEXT NOT NULL,state TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,plan_id TEXT NOT NULL,day TEXT NOT NULL,flow TEXT NOT NULL,due TEXT NOT NULL,rank INTEGER NOT NULL,payload TEXT NOT NULL,state TEXT NOT NULL,context TEXT NOT NULL,attempt INTEGER NOT NULL DEFAULT 0,active_attempt TEXT,error TEXT,outer TEXT);
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,at TEXT NOT NULL,kind TEXT NOT NULL,task_id TEXT,data TEXT NOT NULL);
        ''');self.db.commit()
    def close(self):self.db.close()
    @contextlib.contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:yield;self.db.commit()
        except BaseException:self.db.rollback();raise
    def event(self,kind,task=None,**data):self.db.execute('INSERT INTO events(at,kind,task_id,data) VALUES(?,?,?,?)',(now(),kind,task,json.dumps(data,ensure_ascii=False)))
    def get(self,key,default=None):
        r=self.db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone();return json.loads(r[0]) if r else default
    def set(self,key,value):self.db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',(key,json.dumps(value)))
    def task(self,key):
        row=self.db.execute('SELECT * FROM tasks WHERE id=?',(key,)).fetchone();need(row is not None,'task-not-found');return self.decode(row)
    def decode(self,row):
        r=dict(row)
        for k in ('payload','context','outer'):r[k]=json.loads(r[k]) if r.get(k) else None
        return r
    def tasks(self):return [self.decode(r) for r in self.db.execute('SELECT * FROM tasks ORDER BY due,rank,id')]
    def plans(self):return [{'id':r['id'],'state':r['state'],**json.loads(r['payload'])} for r in self.db.execute('SELECT * FROM plans ORDER BY id')]
    def update(self,key,**values):
        for k in ('context','outer'):
            if k in values:values[k]=json.dumps(values[k],ensure_ascii=False)
        need(set(values)<={'state','context','attempt','active_attempt','error','outer'},'invalid-task-update')
        self.db.execute('UPDATE tasks SET '+','.join(k+'=?' for k in values)+' WHERE id=?',(*values.values(),key))
