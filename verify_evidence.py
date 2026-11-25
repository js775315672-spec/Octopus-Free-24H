import hashlib,json,os,sys
from pathlib import Path
p=Path(sys.argv[1]); raw=(p/"inference.json").read_bytes()
digest=hashlib.sha256(raw).hexdigest()
if digest!=sys.argv[2]: raise SystemExit("digest mismatch")
s=json.loads(raw)
if s["run_id"]!=os.environ["GITHUB_RUN_ID"] or s["head_sha"]!=os.environ["GITHUB_SHA"]: raise SystemExit("provenance mismatch")
if s["model_sha256"]!="cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046": raise SystemExit("model mismatch")
print("INDEPENDENT_EVIDENCE_PASS",digest)
