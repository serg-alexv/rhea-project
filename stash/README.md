# RHEA leftovers archive

This directory on branch **`stash`** preserves supplied evidence and records work that still needs collecting from WD. It is an archive, not an implementation baseline or an acceptance verdict. The branch name is literal; this is not Git's local `git stash` mechanism.

**Current collection: `2026-09-06-cloud-001` — `PARTIAL_WD_UNAVAILABLE`.**

The active collection runtime reports Linux `localhost`. No WD filesystem mount or usable WD connection is available in this session. The original three uploaded maps and the prepared report are available as files. Their bytes are preserved exactly. A separate structured record retains the subsequently supplied binary-provenance findings; it is a derivative of a user message, not a copy of a missing original file.

- [Current run and receipt boundaries](runs/2026-09-06-cloud-001/README.md)
- [Object manifest](runs/2026-09-06-cloud-001/manifest.json)
- [WD collection queue](runs/2026-09-06-cloud-001/pending.json)
- [Repeatable preservation procedure](protocol/LEFTOVER_PRESERVATION.md)
- [Versioned task genome](protocol/task-genome.json)
- [Instruction to resume on WD](protocol/RESUME_ON_WD.md)
- [Protocol changes](protocol/CHANGELOG.md)

Objects are addressed by SHA-256. Filenames and evidence classes are in the run manifest; an identical object is stored once and may have several source locators. Existing project files outside `stash/` are inherited from the parent commit and are **not** evidence collected by this run.

The cross-project report belongs in `v2/01_contracts/evidence/audits/2026-09-06-wd-provenance/report.md` on a documentation PR targeting `rhea-project-v2`. Promote individual reviewed documents or patches from this archive when appropriate. Do not merge this whole archival branch into v2 or component repositories.

Binary, VM, source-tree and conversation paths in a map are locators until their actual bytes and storage receipts are obtained. A recorded hash alone is not a backup. Preservation, public publication, source integration and executed qualification are separate states.
