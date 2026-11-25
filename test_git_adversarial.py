import unittest
from unittest.mock import patch, MagicMock
from git_ledger import Ledger, Conflict
import test_git_ledger as fixtures

class AdversarialTests(unittest.TestCase):
    def test_future_clock(self):
        l=Ledger("https://github.com/js775315672-spec/Octopus-Free-24H.git")
        response=MagicMock()
        response.__enter__.return_value.headers={"Date":"Thu, 01 Jan 1970 00:01:40 GMT"}
        with patch("git_ledger.urllib.request.urlopen",return_value=response), patch("git_ledger.time.time",return_value=10000):
            with self.assertRaisesRegex(Conflict,"clock skew"): l.trusted_time()
    def test_forged_state(self):
        for state in [dict(owner=None,expiry=1,fence=0,version=0,checkpoint={}),dict(owner=None,expiry=0,fence=9,version=1,checkpoint={}),dict(owner=None,expiry=float("nan"),fence=0,version=0,checkpoint={})]:
            with self.assertRaises(Conflict): Ledger.validate(state)
    def test_stolen_owner_wrong_fence(self):
        f=fixtures.LedgerTests(); f.setUp(); self.addCleanup(f.doCleanups)
        h,s=f.l.transact(f.head,"acquire","owner")
        for owner,fence in [("intruder",1),("owner",0),("owner",True)]:
            with self.assertRaises(Conflict): f.l.transact(h,"checkpoint",owner,fence,payload={})
        self.assertEqual(f.l.git(f.remote,"rev-parse",f.l.ref),h)
    def test_timeout_after_push(self):
        import subprocess
        f=fixtures.LedgerTests(); f.setUp(); self.addCleanup(f.doCleanups)
        original=f.l.git
        def lose(cwd,*args,**kwargs):
            result=original(cwd,*args,**kwargs)
            if args[0]=="push": raise subprocess.TimeoutExpired("git push",30)
            return result
        with patch.object(f.l,"git",side_effect=lose):
            h,s=f.l.transact(f.head,"acquire","owner")
        self.assertEqual(f.l.git(f.remote,"rev-parse",f.l.ref),h)
