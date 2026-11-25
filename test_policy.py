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

    def test_workspace(self):
        import tempfile
        from pathlib import Path
        from octopus_policy import authorize_workspace
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"candidates").mkdir()
            args=(root,"js775315672-spec/Octopus-Free-24H","dev/test")
            self.assertTrue(authorize_workspace(*args,["candidates/new.py"]))
            (root/"outside.py").write_text("protected")
            (root/"candidates/link.py").symlink_to(root/"outside.py")
            (root/"candidates/dir").symlink_to(root, target_is_directory=True)
            (root/"candidates/folder.py").mkdir()
            for path in ["candidates/link.py","candidates/dir/outside.py","candidates/folder.py"]:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    authorize_workspace(*args,[path])
            import os
            os.link(root/"outside.py",root/"candidates/hard.py")
            with self.assertRaises(ValueError):
                authorize_workspace(*args,["candidates/hard.py"])
