import unittest,time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
import test_git_ledger as fixtures
from git_ledger import Conflict

class StressTests(unittest.TestCase):
    def test_90_rounds(self):
        for n in (5,10,20):
            start=time.monotonic()
            wins=blocked=0
            for round_id in range(30):
                fixture=fixtures.LedgerTests()
                fixture.setUp()
                try:
                    gate=Barrier(n)
                    def worker(i):
                        gate.wait(timeout=30)
                        try: return fixture.l.transact(fixture.head,"acquire",str(i))
                        except Conflict: return None
                    with ThreadPoolExecutor(max_workers=n) as pool:
                        results=list(pool.map(worker,range(n)))
                    accepted=[x for x in results if x is not None]
                    self.assertEqual(len(accepted),1)
                    self.assertEqual(fixture.l.git(fixture.remote,"rev-parse",fixture.l.ref),accepted[0][0])
                    wins+=len(accepted)
                    blocked+=n-len(accepted)
                finally:
                    fixture.doCleanups()
            print(f"CAS_STRESS workers={n} rounds=30 wins={wins} blocked={blocked} seconds={time.monotonic()-start:.3f}",flush=True)
    def test_clock_regression(self):
        f=fixtures.LedgerTests(); f.setUp(); self.addCleanup(f.doCleanups)
        with patch("git_ledger.time.time",return_value=100):
            h,s=f.l.transact(f.head,"acquire","a")
        with patch("git_ledger.time.time",return_value=99):
            with self.assertRaises(Conflict): f.l.transact(h,"renew","a",s["fence"])
    def test_lost_response(self):
        f=fixtures.LedgerTests(); f.setUp(); self.addCleanup(f.doCleanups)
        original=f.l.git
        def lose(cwd,*args,**kwargs):
            result=original(cwd,*args,**kwargs)
            if args[0]=="push": raise Conflict("simulated lost response")
            return result
        with patch.object(f.l,"git",side_effect=lose):
            h,s=f.l.transact(f.head,"acquire","a")
        self.assertEqual(f.l.git(f.remote,"rev-parse",f.l.ref),h)
        self.assertEqual(s["fence"],1)
