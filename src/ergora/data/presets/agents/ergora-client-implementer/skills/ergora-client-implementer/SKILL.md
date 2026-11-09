---
name: ergora-client-implementer
description: client api guidance for the selected workflow instance.
---

Use real transport and serialization owners. Compare old/new responses, pagination continuation, cancellation and error handling. Keep compatibility differences local to the consumer adapter; avoid duplicating orchestration or silently discarding unsupported fields. Add only necessary regression coverage for the supported contract.
