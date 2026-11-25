"""P2 Git CAS ledger prototype. Trusted publishers and synchronized clocks only.
Use an explicitly provisioned dedicated ledger branch; never main or DEV.
"""
import json, subprocess, tempfile, time, math, urllib.request, email.utils, secrets
from pathlib import Path

class Conflict(RuntimeError): pass
class ClockConflict(Conflict): pass

class Ledger:
    ref="refs/heads/octopus-test-ledger"
    def __init__(self, remote):
        self.remote=str(remote)
    def trusted_time(self):
        if self.remote != "https://github.com/js775315672-spec/Octopus-Free-24H.git":
            return time.time()
        try:
            req=urllib.request.Request("https://api.github.com/?octopus_nonce="+secrets.token_hex(16), headers={"Cache-Control":"no-cache, no-store","User-Agent":"octopus-ledger"})
            with urllib.request.urlopen(req,timeout=10) as response:
                stamp=email.utils.parsedate_to_datetime(response.headers["Date"]).timestamp()
            if abs(time.time()-stamp)>15: raise ClockConflict("clock skew")
            return time.time()
        except Conflict: raise
        except Exception as exc: raise ClockConflict("trusted clock unavailable") from exc
    @staticmethod
    def validate(s):
        if not isinstance(s,dict) or set(s)-{"owner","expiry","fence","version","checkpoint","last_time"} or not {"owner","expiry","fence","version","checkpoint"}<=set(s): raise Conflict("state schema")
        for k in ("fence","version"):
            if type(s[k]) is not int or s[k]<0: raise Conflict("state counter")
        if s["fence"]>s["version"]: raise Conflict("fence exceeds version")
        for k in ("expiry","last_time"):
            v=s.get(k,0)
            if type(v) not in (int,float) or not math.isfinite(v) or v<0: raise Conflict("state time")
        if s["owner"] is None:
            if s["expiry"]!=0: raise Conflict("unowned lease")
        elif not isinstance(s["owner"],str) or not s["owner"] or s["fence"]==0 or s["expiry"]<=s.get("last_time",0) or s["expiry"]-s.get("last_time",0)>3600: raise Conflict("invalid lease")
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
            self.validate(s)
            now=self.trusted_time()
            if now<s.get("last_time",0): raise Conflict("clock regression")
            s["last_time"]=now
            if action=="acquire":
                if s["owner"] is not None and s["expiry"]>now: raise Conflict("busy")
                s.update(owner=owner,fence=s["fence"]+1,expiry=now+ttl)
            else:
                if type(fence) is not int or s["owner"]!=owner or s["fence"]!=fence or s["expiry"]<=now: raise Conflict("stale lease")
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
                if observed!=commit:
                    try: self.git(d,"merge-base","--is-ancestor",commit,observed)
                    except Conflict: raise Conflict("push outcome uncertain or competing head")
            return commit,s
