"""Trusted CI integration only. No candidate code is executed."""
import os,sys,base64,tempfile,json,time
from git_ledger import Ledger,Conflict,ClockConflict
REMOTE="https://github.com/js775315672-spec/Octopus-Free-24H.git"
def main():
    if os.environ.get("GITHUB_REPOSITORY")!="js775315672-spec/Octopus-Free-24H": raise RuntimeError("wrong repo")
    token=os.environ.pop("TOKEN")
    os.environ.update(GIT_CONFIG_COUNT="1",GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",GIT_CONFIG_VALUE_0="AUTHORIZATION: basic "+base64.b64encode(("x-access-token:"+token).encode()).decode(),GIT_TERMINAL_PROMPT="0")
    l=Ledger(REMOTE)
    baseline=os.environ["BASELINE"]
    prefix=os.environ["GITHUB_RUN_ID"]+":"+os.environ["GITHUB_RUN_ATTEMPT"]+":"
    def snapshot():
        with tempfile.TemporaryDirectory() as d:
            l.git(d,"init","-q")
            l.git(d,"fetch","--no-tags",REMOTE,l.ref)
            h=l.git(d,"rev-parse","FETCH_HEAD")
            return h,json.loads(l.git(d,"show",h+":state.json")),l.git(d,"rev-parse",h+"^")
    if sys.argv[1]=="race":
        owner=prefix+os.environ["WORKER"]
        try:
            h,s=l.transact(baseline,"acquire",owner,ttl=120)
            print("REMOTE_WIN",h,s["fence"],flush=True)
        except ClockConflict:
            raise
        except Conflict:
            for attempt in range(6):
                h,s,parent=snapshot()
                if parent==baseline and str(s["owner"]).startswith(prefix):
                    print("REMOTE_BLOCK",h,flush=True)
                    break
                if h!=baseline: raise RuntimeError("unexpected ledger transition")
                time.sleep(1)
            else: raise RuntimeError("unverified conflict")
    else:
        h,s,parent=snapshot()
        if parent!=baseline or not str(s["owner"]).startswith(prefix): raise RuntimeError("no unique winning child")
        old=s["owner"]; fence=s["fence"]
        delay=max(0,s["expiry"]-time.time()+1)
        if delay>125: raise RuntimeError("clock skew")
        time.sleep(delay)
        h,s=l.transact(h,"acquire",prefix+"recovery",ttl=60)
        assert s["fence"]==fence+1
        try: l.transact(h,"checkpoint",old,fence,payload={})
        except ClockConflict: raise
        except Conflict: pass
        else: raise RuntimeError("stale fence accepted")
        h,s=l.transact(h,"renew",prefix+"recovery",s["fence"],ttl=60)
        h,s=l.transact(h,"checkpoint",prefix+"recovery",s["fence"],payload={"run":prefix})
        h,s=l.transact(h,"release",prefix+"recovery",s["fence"])
        print("REMOTE_RECOVERY_PASS",h,s["fence"],flush=True)
if __name__=="__main__": main()
