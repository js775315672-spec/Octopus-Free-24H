"""P2 Git CAS ledger prototype. Trusted publishers and synchronized clocks only.
Use an explicitly provisioned dedicated ledger branch; never main or DEV.
"""
import json, subprocess, tempfile, time
from pathlib import Path

class Conflict(RuntimeError): pass

class Ledger:
    ref="refs/heads/octopus-test-ledger"
    def __init__(self, remote):
        self.remote=str(remote)
    def git(self, cwd, *args, data=None):
        p=subprocess.run(["git","-C",str(cwd),*args],input=data,text=True,capture_output=True,timeout=30)
        if p.returncode: raise Conflict(p.stderr[:500])
        return p.stdout.strip()
    def transact(self, expected, action, owner, fence=0, ttl=60, payload=None):
        if not isinstance(owner,str) or not owner or not 0<ttl<=3600: raise ValueError("lease")
        with tempfile.TemporaryDirectory() as d:
            self.git(d,"init","-q")
            self.git(d,"fetch","--no-tags",self.remote,self.ref)
            head=self.git(d,"rev-parse","FETCH_HEAD")
            if head!=expected: raise Conflict("head changed")
            s=json.loads(self.git(d,"show",head+":state.json"))
            now=time.time()
            if now<s.get("last_time",0): raise Conflict("clock regression")
            s["last_time"]=now
            if action=="acquire":
                if s["owner"] is not None and s["expiry"]>now: raise Conflict("busy")
                s.update(owner=owner,fence=s["fence"]+1,expiry=now+ttl)
            else:
                if s["owner"]!=owner or s["fence"]!=fence or s["expiry"]<=now: raise Conflict("stale lease")
                if action=="renew": s["expiry"]=now+ttl
                elif action=="checkpoint": s["checkpoint"]=payload
                elif action=="release": s.update(owner=None,expiry=0)
                else: raise ValueError("action")
            s["version"]+=1
            data=json.dumps(s,sort_keys=True,allow_nan=False)
            if len(data)>65536: raise ValueError("state too large")
            blob=self.git(d,"hash-object","-w","--stdin",data=data)
            tree=self.git(d,"mktree",data="100644 blob "+blob+"\tstate.json\n")
            commit=self.git(d,"-c","user.name=Octopus","-c","user.email=octopus@example.invalid","commit-tree",tree,"-p",head,data="ledger transition\n")
            # No force: competing children cannot both fast-forward.
            try:
                self.git(d,"push",self.remote,commit+":"+self.ref)
            except (Conflict, subprocess.TimeoutExpired):
                # A lost response is not a failed commit if the exact commit is present.
                self.git(d,"fetch","--no-tags",self.remote,self.ref)
                observed=self.git(d,"rev-parse","FETCH_HEAD")
                if observed!=commit: raise Conflict("push outcome uncertain or competing head")
            return commit,s
