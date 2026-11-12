# Throwaway process supervision experiment

Question: can the existing supervised process implementation stop an entire dedicated job after preparation has already consumed part of one fixed wall budget, including a blocked file lock and a descendant that created a new session?

With Python 3.11+ and Ergora installed, run on Linux:

```bash
python docs/prototypes/six-stage-budget/process-probe-prototype.py ./NEW_PROTOTYPE_DIRECTORY
```

This prototype uses real subprocesses, a real POSIX lock and the existing `ergora.processes` subreaper. The scratch directory must be new. It contains three cases and rereads the same budget after its productive cutoff. `observed-r2.json` preserves the observed timings and process identities; `provenance.json` identifies the exact script and original process implementation. The observer records any manual cleanup and rejects a pass if it had to stop a process itself.

The observed cases support this process seam for further investigation. No product budget, task prepare/create/start, Temporal scheduling, Git operation, model call slot or formal receipt finalization was exercised. Bounded cleanup failures and uninterruptible I/O remain unverified. The first diagnostic omitted a separate manual-cleanup counter; r2 added that counter and retained the first diagnostic privately.

Keep this experiment on the prototype branch. Production decisions and remaining acceptance live in the development branch B2 plan; the script is not a product module or CI test.
