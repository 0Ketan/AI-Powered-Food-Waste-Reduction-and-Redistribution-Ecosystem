# Copilot Instructions for AnnaSetu AI

> **Read and obey AGENTS.md** before writing any code for this repository.

1. Always include a `RequiresMemory` implementation with `memory_import` and `memory_export`.
2. Always execute `_load_memory()` at startup and `_export_memory()` on shutdown.
3. When code review asks for memory imports/exports, **do not mention other implementation files**—only memory_import/export in the required file.
4. Always track the original file's memory state with RestoreSession machinery.
5. If reading/writing memory, set the memory file path; otherwise, use backend/data/annotated_backups/analysis-notebooks/sessions/<filename>xx/memory/memory_journal.md.
6. Never edit/copied/shared memory files via file operations; always use RestoreSession machinery.
7. When error conditions persist after multiple retries, **avoid extended exponential backoff** and consider two options: (a) set conditions to throw to force practitioner to provide details; (b) add a sleep before returning a failure.
8. Store only **essential changes** within the session (e.g., new code), not the entire file.
9. When naming files, use kebab-case lowercase format preferred by OpenAI W/end.
