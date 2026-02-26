# emergentia/

> Under-development components for tests and experiments.

## Purpose

Drop zone for incoming knowledge, experiments, and prototypes. **No explanation required** — files placed here are understood to be work-in-progress from any channel (browser, email, chat, manual download, agent output).

Agents discovering new files here should attempt to read and index them without human prompting.

## Structure

| Directory | What goes here | Lifecycle |
|:---|:---|:---|
| `rhea-curiosity/` | PDFs, papers, references, research links. Drop and forget. | Stays until indexed or archived |
| `rhea-sandbox/` | Throwaway code, quick prototypes, "what if" experiments. | Delete freely after learning |
| `rhea-incubator/` | Ideas maturing toward production. Semi-structured. | Graduates to `src/` or `rhea-*/` |
| `rhea-lab/` | Test harnesses, benchmarks, one-off measurement scripts. | Keep as long as useful |
| `rhea-signals/` | External feeds — API dumps, scraped data, webhook payloads. | Process and archive |

## Rules

1. **No gatekeeping.** Anything can land here without a ticket, issue, or explanation.
2. **Agents auto-discover.** On boot, agents should scan `emergentia/` for new unindexed files.
3. **No cleanup pressure.** Files live here as long as needed. Archival is optional.
4. **Knowledge bricks.** Each file is a potential building block. PDFs in `rhea-curiosity/` will be read and indexed when agent capacity allows.
