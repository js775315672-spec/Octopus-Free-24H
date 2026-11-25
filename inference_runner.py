"""P1: local inference only. Output is untrusted data, never executed."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

def digest(path):
    with open(path,"rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()

def verify(path, expected):
    if not re.fullmatch(r"[0-9a-f]{64}",expected) or digest(path)!=expected:
        raise ValueError("digest mismatch")

def infer(binary, model, binary_sha, model_sha, prompt):
    binary,model=Path(binary).resolve(strict=True),Path(model).resolve(strict=True)
    verify(binary,binary_sha)
    verify(model,model_sha)
    if len(prompt)>4096:
        raise ValueError("prompt too long")
    start=time.monotonic()
    result=subprocess.run([str(binary),"-m",str(model),"-p",prompt,"-n","64","-t","2","-c","1024","--seed","42","--temp","0","--no-display-prompt"],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=120,check=True,env={"PATH":"/usr/bin:/bin","LANG":"C.UTF-8"})
    if not result.stdout.strip():
        raise ValueError("empty inference")
    return {"model_sha256":model_sha,"binary_sha256":binary_sha,"seconds":time.monotonic()-start,"output":result.stdout[:8192],"run_id":os.getenv("GITHUB_RUN_ID"),"head_sha":os.getenv("GITHUB_SHA")}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    for arg in ("binary","model","binary_sha","model_sha"):
        p.add_argument(arg)
    a=p.parse_args()
    print(json.dumps(infer(a.binary,a.model,a.binary_sha,a.model_sha,"Suggest one test for a Python function that adds two integers.")))
