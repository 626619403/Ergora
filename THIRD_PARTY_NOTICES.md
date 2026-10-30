# Third-party sources

Ergora's own license is pending maintainer selection. This does not change the
licenses of the third-party components listed below.

## Bundled browser component

`src/ergora/data/console/vendor/cytoscape.min.js` is Cytoscape.js **3.33.1**,
from [cytoscape/cytoscape.js](https://github.com/cytoscape/cytoscape.js),
distributed under the MIT license. Copyright 2016–2025 The Cytoscape Consortium.
The original header is retained, and the complete license is in
[CYTOSCAPE-LICENSE.txt](src/ergora/data/console/vendor/CYTOSCAPE-LICENSE.txt).

## Frozen reference distribution

`src/ergora/data/reference/` preserves the files embedded in the public v2.2
HTML distribution. [reference-manifest.json](src/ergora/data/reference-manifest.json)
records each file's SHA-256 and the source archive SHA-256; `ergora reference
verify` checks that identity. The original archive and upstream documentation
are retained for comparison. The project does not assign a new license to
material whose original license has not been established.

The reference installers download external tools rather than including their
installed distributions. Versions and download identities are recorded in
[BUNDLE-MANIFEST.json](src/ergora/data/reference/BUNDLE-MANIFEST.json), the
reference dependency locks, and the bootstrap scripts. Each external project
retains its own license. Source provenance is not a claim that the reference
bundle has a single blanket open-source license.

## Optional dependencies and tools

FastAPI, Uvicorn, PyYAML, GEPA, Temporal, and other SDKs are installed from their
own distributions. Codex, Claude Code, ReMe, and optional agent tools are not
relicensed or bundled by naming an adapter. Consult each installed package or
upstream repository for its license and notices. Authentication, model access,
and any model or GPU charges are configured by the operator.
