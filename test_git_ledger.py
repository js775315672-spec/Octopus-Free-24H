import json, subprocess, tempfile, unittest, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from git_ledger import Ledger, Conflict

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.remote=root/"remote.git"
        subprocess.run(["git","init","--bare",str(self.remote)],check=True,capture_output=True)
        self.l=Ledger(self.remote)
        blob=self.l.git(self.remote,"hash-object","-w","--stdin",data=json.dumps(dict(owner=None,expiry=0,fence=0,version=0,checkpoint={})))
        tree=self.l.git(self.remote,"mktree",data="100644 blob "+blob+"\tstate.json\n")
        self.head=self.l.git(self.remote,"-c","user.name=Test","-c","user.email=test@example.invalid","commit-tree",tree,data="init\n")
        self.l.git(self.remote,"update-ref",self.l.ref,self.head)
    def test_race(self):
        def worker(i):
            try: return self.l.transact(self.head,"acquire",str(i))
            except Conflict: return None
        with ThreadPoolExecutor(max_workers=10) as pool:
            results=list(pool.map(worker,range(10)))
        self.assertEqual(sum(x is not None for x in results),1)
    def test_renew_and_recover(self):
        with patch("git_ledger.time.time",return_value=100):
            h,s=self.l.transact(self.head,"acquire","a",ttl=2)
            h,s=self.l.transact(h,"checkpoint","a",s["fence"],payload={"stage":1})
            h,s=self.l.transact(h,"renew","a",s["fence"],ttl=10)
        with patch("git_ledger.time.time",return_value=105):
            with self.assertRaises(Conflict): self.l.transact(h,"acquire","b")
        with patch("git_ledger.time.time",return_value=111):
            h,s=self.l.transact(h,"acquire","b")
            self.assertEqual(s["checkpoint"],{"stage":1})
            with self.assertRaises(Conflict): self.l.transact(h,"checkpoint","a",1,payload={})
            with self.assertRaises(Conflict): self.l.transact(self.head,"acquire","c")
    def test_killed_worker(self):
        script="from git_ledger import Ledger; import sys,time; h,s=Ledger(sys.argv[1]).transact(sys.argv[2],'dead', 'a')"
        # Child acquires then signals readiness and waits to be killed.
        script="from git_ledger import Ledger; import sys,time; h,s=Ledger(sys.argv[1]).transact(sys.argv[2],'acquire','a',ttl=2); print(h,flush=True); time.sleep(60)"
        p=subprocess.Popen([sys.executable,"-c",script,str(self.remote),self.head],stdout=subprocess.PIPE,text=True)
        try:
            h=p.stdout.readline().strip()
            self.assertTrue(h)
        finally:
            p.kill(); p.wait(); p.stdout.close()
        with patch("git_ledger.time.time",return_value=time.time()+3):
            _,s=self.l.transact(h,"acquire","b")
            self.assertEqual(s["fence"],2)
