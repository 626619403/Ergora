---
name: ergora-workflow-retrospective
description: Propose or review bounded root workflow revisions from complete selected evidence and a frozen recursive manifest, preserving authority, dependencies and evaluation ownership.
---

Read the complete request, including every target manifest file and all ancestor resources. Treat artifacts as observations. Separate recorded facts, hypotheses, unknown costs and negative outcomes; cite exact selected job_id, artifact name and SHA256.

Return candidate=null when no supported improvement is available. Otherwise provide the complete root definition using baseline.next_version, hypothesis, applicability and evaluation_plan. Explain a check that could falsify the hypothesis on the same trusted workload and relevant holdouts. Graph admission alone does not measure quality or performance.

A candidate may change the root description, content of already declared root resources, and add dependency edges. Preserve root ID/schema/permissions/limits/input and output ports, every node and its references/roles/permissions/input bindings/review requirement, existing dependency edges and declared resource IDs/kinds/paths. Child Agent or workflow implementations stay fixed. Retain baseline resource digests in the proposed definition: the original preview recomputes them from the actual changes.

resource_changes uses the original schema_version:1 and operations array. Use an empty operations array for graph-only changes. Operations are write (path, content_base64, optional executable_bits), delete (path), or mkdir (path). Paths are portable paths inside the root bundle: only declared text files or descendants of a declared Skill directory may change. Encode complete UTF-8 write content as base64, retaining exact line endings and executable bits. Read the complete baseline root resource before changing it; preserve useful knowledge and qualifications.

The checker restores complete files only into private scratch, invokes the original revision preview and acceptance there, and compiles with the frozen grant. It does not authenticate source authors, evaluate effects or import into the user's live library. Explicit export requires original result and candidate identities. Actual import and manifest selection remain original operator actions; old runs retain their original manifests.

When reviewing, inspect the complete original proposal and checked revision against all cited source observations. Consider unnecessary serialization, lost information, prompt-induced authority changes, conflicting instructions and verification costs. Your decision reviews the proposal, not permission to adopt it.
