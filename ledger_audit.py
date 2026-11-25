"""Read-only audit of every transition since the pinned test-ledger genesis."""
import json, subprocess, sys
from git_ledger import Ledger
GENESIS="fb79b7b3f4268f45e116e08867d93b6e979482b0"
def audit(root, head, genesis=GENESIS):
    def git(*args):
        return subprocess.check_output(["git","-C",root,*args],text=True,timeout=30).strip()
    chain=git("rev-list","--first-parent",head).splitlines()
    if genesis not in chain: raise ValueError("missing genesis")
    chain=list(reversed(chain[:chain.index(genesis)+1]))
    prev=None
    for sha in chain:
        if git("ls-tree","--name-only",sha)!="state.json": raise ValueError("unexpected tree")
        s=json.loads(git("show",sha+":state.json")); Ledger.validate(s)
        if prev is None:
            if s["version"]!=0 or s["fence"]!=0 or s["owner"] is not None: raise ValueError("genesis")
        else:
            p,old=prev
            if git("rev-list","--parents","-n","1",sha).split()!=[sha,p]: raise ValueError("parent")
            now=s["last_time"]
            if s["version"]!=old["version"]+1 or now<old.get("last_time",0): raise ValueError("sequence")
            delta=s["fence"]-old["fence"]
            if delta==1:
                if s["owner"] is None or (old["owner"] is not None and old["expiry"]>now) or s["checkpoint"]!=old["checkpoint"]: raise ValueError("acquire")
            elif delta==0:
                if old["owner"] is None or old["expiry"]<=now: raise ValueError("expired writer")
                if s["owner"] is None:
                    if s["checkpoint"]!=old["checkpoint"]: raise ValueError("release")
                elif s["owner"]!=old["owner"] or (s["expiry"]!=old["expiry"] and s["checkpoint"]!=old["checkpoint"]): raise ValueError("mutation")
            else: raise ValueError("fence")
        prev=(sha,s)
    return len(chain)-1
if __name__=="__main__":
    print("LEDGER_AUDIT_PASS",sys.argv[2],audit(sys.argv[1],sys.argv[2]))
