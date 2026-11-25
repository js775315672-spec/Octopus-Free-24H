"""Trusted single-host SQLite state store; not a distributed GitHub lease."""
import sqlite3
import json
import time
from contextlib import contextmanager

class Conflict(RuntimeError): pass

class Store:
    def __init__(self,path):
        self.path=str(path)
        with self.tx() as c:
            c.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL, fence INTEGER NOT NULL, owner TEXT, expiry REAL NOT NULL, checkpoint TEXT NOT NULL)")
            c.execute("INSERT OR IGNORE INTO state VALUES (1,0,0,NULL,0,'{}')")
    @contextmanager
    def tx(self):
        c=sqlite3.connect(self.path,timeout=10,isolation_level=None)
        try:
            c.execute("PRAGMA synchronous=FULL")
            c.execute("BEGIN IMMEDIATE")
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()
    def read(self):
        with self.tx() as c:
            v,f,o,e,p=c.execute("SELECT version,fence,owner,expiry,checkpoint FROM state").fetchone()
            return v,f,o,e,json.loads(p)
    def acquire(self,owner,ttl):
        if not isinstance(owner,str) or not owner or not 0<ttl<=3600: raise ValueError("lease")
        with self.tx() as c:
            now=time.time()
            v,f,o,e=c.execute("SELECT version,fence,owner,expiry FROM state").fetchone()
            if o is not None and e>now: raise Conflict("busy")
            c.execute("UPDATE state SET fence=?,owner=?,expiry=? WHERE id=1",(f+1,owner,now+ttl))
            return v,f+1
    def checkpoint(self,owner,fence,expected,payload):
        data=json.dumps(payload,allow_nan=False,sort_keys=True)
        if len(data)>65536: raise ValueError("checkpoint too large")
        with self.tx() as c:
            cur=c.execute("UPDATE state SET version=version+1,checkpoint=? WHERE id=1 AND owner=? AND fence=? AND version=? AND expiry>?",(data,owner,fence,expected,time.time()))
            if cur.rowcount!=1: raise Conflict("stale or expired")
            return expected+1
    def release(self,owner,fence):
        with self.tx() as c:
            cur=c.execute("UPDATE state SET owner=NULL,expiry=0 WHERE id=1 AND owner=? AND fence=? AND expiry>?",(owner,fence,time.time()))
            if cur.rowcount!=1: raise Conflict("stale or expired")
