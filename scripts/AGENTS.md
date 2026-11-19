# Script change entry point

Before changing installation, upgrade, runtime, or CI scripts, read the [scripts and checks protocol](../docs/architecture/component-change-protocols.md#scripts-and-checks), then follow the domain owners called by the script to check parameters, persistent paths, platform support, and recovery contracts.

Scripts consume existing library interfaces; reusable behavior belongs to its actual owner, avoiding another implementation of configuration selection, scoring, or approval. When changing observable installation/platform behavior, select existing installation seams; when changing only explanatory text, check links and ensure commands match actual entry points. Maintain version/fixed-source/license information under the original tool installation contract.
