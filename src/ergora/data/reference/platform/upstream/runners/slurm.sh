#!/usr/bin/env bash
set -euo pipefail
# sbatch --exclusive --nodes=<N> --ntasks-per-node=1 --gpus-per-node=<G> #   --time=<HH:MM:SS> runners/slurm.sh /absolute/kit /absolute/manifest.json
# Site partition/account/QoS/CPU/memory settings belong in the project adapter.
: "${SLURM_JOB_ID:?Run inside an approved Slurm allocation}"
kit_path="$1"
manifest_path="$2"
# The adapter must use the existing verified launcher (e.g. srun + torchrun),
# preserve all-rank outputs, and return nonzero for failures. This is not torchrun itself.
python3 "$kit_path/adapters/project_adapter.py" measure --manifest "$manifest_path"
