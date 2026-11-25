import tempfile, unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from state_store import Store, Conflict

class StateTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.path=Path(self.d.name)/"state.db"
        self.s=Store(self.path)
    def test_cas(self):
        v,f=self.s.acquire("a",60)
        self.assertEqual(self.s.checkpoint("a",f,v,{"stage":1}),1)
        with self.assertRaises(Conflict): self.s.checkpoint("a",f,v,{})
        self.assertEqual(Store(self.path).read()[-1],{"stage":1})
    def test_expiry_recovery(self):
        with patch("state_store.time.time",return_value=100):
            v,f=self.s.acquire("a",1)
            self.s.checkpoint("a",f,v,{"stage":1})
        with patch("state_store.time.time",return_value=102):
            v,g=Store(self.path).acquire("b",60)
            self.assertGreater(g,f)
            with self.assertRaises(Conflict): self.s.checkpoint("a",f,v,{})
            with self.assertRaises(Conflict): self.s.release("a",f)
            self.assertEqual(self.s.read()[-1],{"stage":1})
    def test_contention(self):
        def worker(i):
            try: return Store(self.path).acquire(str(i),60)
            except Conflict: return None
        with ThreadPoolExecutor(max_workers=20) as pool:
            results=list(pool.map(worker,range(20)))
        self.assertEqual(sum(x is not None for x in results),1)
    def test_rollback(self):
        with self.assertRaises(RuntimeError):
            with self.s.tx() as c:
                c.execute("UPDATE state SET version=99")
                raise RuntimeError()
        self.assertEqual(self.s.read()[0],0)
