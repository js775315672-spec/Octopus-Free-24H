# OCTOPUS dashboard
P1 CPU inference PASS: run 45536642913 job 138944759355, head 1b813bba60c53c80c8725beb54347fe6456b9c58, merge db5eac23edf8dc1d9bdd960866f0f1f762a2c136, 3.849692677 seconds. Logged JSON digest a2b8950282eb815da4dede0fba02ae79628b3c9cd6c66b1ff640444a4f1f434e; original artifact not independently retrieved.
P2 single-host SQLite prototype: CI pending. Distributed persistence and crash tests pending. Evolution 0. Schedule not enabled.

2026-11-25: remote integration run 45550101481 passed; recovery job 138989077821, final commit 98f9783b7e3f6d7000b1b4101807741defc051ba, fence 2. Run 45551045387 failed job 138992073046: clock skew then unverified conflict; recovery skipped. Policy run 45551045386 succeeded. Clock source cache-busting and distinct error classification pending CI. P2 blocked; no evolution. Official model source and original artifact independent verification pending.

Run 45562579372 policy PASS 19 tests 23.345s, inference job 139029578238 5.647074114s, logged digest cf64bb882aec566163b8ab421150c4503241134f0163f9421c8aa9549b876d97. Remote run 45562579374 race 1 winner/4 blocked, fence 4; recovery job 139029690380 failed HTTP 403 rate limit. Authenticated clock request fix pending CI. No bypass of clock guard. P2 blocked.

## Verified baseline — 2026-11-25
- DEV 59acd60e66118f33a4f6c82764073dec56cffb15; main e6cf38d8044d42dfedebfab14a93f2a98742d259. Draft PR #1.
- Policy run 45568106220, job 139047777901: 20 tests PASS, 24.205s; CAS 90/90. Inference job 139047777920: 3.060639670s, merge bca152c6ec32dd164163ee41f8625b7dbabba179.
- Model publisher SHA256 cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046 independently matched https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/blob/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf . llama.cpp a7a98e0fffed794396b3fbad4dcdbbc184963645 checkout confirmed in log.
- Logged inference digest 3e3b35f5ce5cdc93b266010c87cd5bb7dce442fdb164ac56624b93a6dc07ca8b. Artifact list empty; original bytes not independently verified.
- Remote run 45568106202: all seven jobs passed, recovery job 139047945746, final logged commit beb7b7da7abe360ca32e4012cf7ca7baadfbd828. Remote state blob 009774b5e018e4b4abd2021846d877cce723df90: fence 6, version 12, owner null, expiry 0, checkpoint run 45568106202:1:. Full parent-chain audit not certified.
- P2 functional CI passed; raw writer credential compromise and full history authentication remain unverified. P0 full execution isolation and P1 original artifact verification pending. P3–P5 blocked. GEN 000. No production schedule or merge.
