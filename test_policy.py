import unittest
from octopus_policy import authorize
class PolicyTests(unittest.TestCase):
    def test_allowed(self):
        self.assertTrue(authorize("js775315672-spec/Octopus-Free-24H","dev/test",["candidates/example.py"]))
    def test_denied(self):
        repo="js775315672-spec/Octopus-Free-24H"
        for r,b,p in [(repo,"main",["candidates/a.py"]),("other/repo","dev/test",["candidates/a.py"]),(repo,"dev/test",[".github/workflows/ci.yml"]),(repo,"dev/test",["candidates/../a.py"]),(repo,"dev/test",["candidates/a\\b.py"]),(repo,"dev/test",[]),(repo,"dev/test",["candidates/a.py","octopus_policy.py"])]:
            with self.subTest(r=r,b=b,p=p), self.assertRaises(ValueError):
                authorize(r,b,p)
