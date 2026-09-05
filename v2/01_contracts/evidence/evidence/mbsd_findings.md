# MBSD: bounded network/isolation extraction

Source: `timelabs-npo/mbsd` at `181f1ea6081ad2998affa9aeda79021b398e0375`. Original 5,220-file snapshot SHA-256: `28abfe7738f192c6a4b2a67f13db09ff9627c10ea1794b5fca1d062035a37d6a`.

The dictionary contains **25 focused records**, selected from **24 files**: 10 files captured in the original snapshot and 14 frozen-source supplements. The remaining 5,210 snapshot files were excluded from semantic enumeration by the routing/process-isolation scope. The repository contains 13,633 tracked paths, of which 13,598 are under `src/sys`. Imported OS volume must not be treated as evidence of architectural centrality or project integration.

All evidence is bound to the frozen commit, source SHA-256, and real source line numbers; snapshot membership is explicit. `mbsd-filter-report.json` lists the selected files, reasons, classifications and hashes. `mbsd-snapshot-filter-index.json` records all 5,220 snapshot paths and selection outcomes. No source build, source test, driver operation, firmware upload, device action, or source mutation was performed.

## Findings and conflicts for the decision map

| ID | Evidence records | Finding | Consequence for synthesis |
|---|---|---|---|
| MBSD.C01 | OS.005, OS.009, OS.010 | Current README/ADR selects an OpenWrt overlay scaffold, while an OpenBSD source tree and GLMT3000 kernel configuration remain. The original custom-OpenBSD framing conflicts with repository product intent. | Preserve distinct OpenBSD research substrate and OpenWrt product-target hypotheses until an explicit baseline decision; do not describe one as already implementing the other. |
| MBSD.C02 | OS.011 | MBSD docs call Rheknel a routing/hardware telemetry bridge. No corresponding integration implementation was found in this MBSD scope. | Reconcile that name against the sibling kernel's actual validation API; do not assign hardware collection authority to a documentation label. |
| MBSD.C03 | OS.015 | No `ollama + rheknel + three models` native executable/linking/packaging contract found in the bounded MBSD search. Ollama is mentioned only as optional host-side build-log assistance. | Native three-model OpenBSD integration remains an extreme-complexity, unverified objective. Sibling repositories must supply their own evidence. |
| MBSD.C04 | OS.014 | `bin/law-core` is a POSIX shell stub. Ten `clause_results` are literal `true`; `overall_pass` uses selected existence/nonempty checks. | Never promote this output into a model tribunal, full clause verification, cryptographic approval, or hardware acceptance receipt. |
| MBSD.C05 | OS.012, OS.013, OS.017 | Checked-in Owner/Codex signature strings are empty, violating the schema's minimum length of 32. Cryptographic verification is a separate optional path that can warn and skip. | Require structural validity and explicit cryptographic verification results as separate gates; an optional skipped check cannot authorize a release. |
| MBSD.C06 | NET.003, NET.008, NET.011, NET.014, NET.015, OS.001–OS.004 | Routing messages, interface counters, pledge/unveil, local peer credentials and PF transaction declarations exist in OpenBSD-derived source. PF/routing structures include platform C types and pointers. | They can inform a proposed platform adapter but cannot be reused as portable network serialization or evidence of an implemented executor. Keep telemetry reads separate from routing/PF mutations. |
| MBSD.C07 | OS.009 | The ImageBuilder script selects a sysupgrade `.itb` or `.bin`, then copies it to two `.itb`-named destinations. | Output names do not verify FIT format, recovery compatibility, signing or successful boot. Those require artifact inspection and target evidence. |
| MBSD.C08 | OS.006, OS.008 | Custom GMAC attachment comments out interface handlers; switch/SPI-NAND attachments are incomplete skeletons. | Declare source scaffolding, not functioning hardware drivers. No target execution occurred. |

## Bounded native-integration search

`git grep -I -n -i -E` over all tracked text at the frozen commit used `rheknel|ollama|tribunal|gguf|llama[._-]?cpp`. There were **7 textual matches**: six documentation references and one unrelated upstream comment containing “judicial tribunal”. The model/runtime filename inventory (`gguf`, `ggml`, `onnx`, `safetensors`, `pt`, `pth`, and named ollama/rheknel/tribunal path components) produced **zero hits**.

The search receipt is `mbsd-integration-search.json`, with exact matched paths/line numbers and no implementations. This is bounded negative evidence for this MBSD commit, not proof that external repositories, local experiments or unpublished binaries do not exist. The dictionary labels it `missing_in_scope`.

## Provenance limits

“OpenBSD-derived baseline” identifies inspected source layout and `$OpenBSD` revision banners. No independently pinned upstream tree was fetched or compared byte for byte, so the classification does not assert that every imported file is unmodified. Custom FDT driver files, their registration entries and GLMT3000 configuration are explicitly classified separately. The source-only supplements repair the original selector's omission of C implementations, shell scripts and Markdown decisions without dumping OS implementations into the main conversation.

No memory-derived implementation or runtime claim is used as evidence. Every current finding above is tied to this frozen source or to the recorded bounded search.
