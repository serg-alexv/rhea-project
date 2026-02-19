# Checklist: Patch Gate (before applying any patch)

- [ ] Patch is provided as: **git apply** patch OR **single copy-paste command**.
- [ ] Patch touches only scoped regions (diff reviewed).
- [ ] Compiles / lints: `python3 -m py_compile ...` (or language equivalent).
- [ ] Has at least one deterministic test (single command).
- [ ] Has a rollback line: `git revert <sha>` or `git checkout -- <files>`.
