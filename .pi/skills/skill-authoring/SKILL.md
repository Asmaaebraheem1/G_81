---
name: skill-authoring
description: Create or update a skill in .pi/skills/ when a repeated workflow, checklist, or domain procedure appears that the current skills do not cover; and route every rules change through agent.md. Use when the same multi-step procedure repeats, when a task needs rules the agent does not have, or when the owner changes a rule.
---

# Skill authoring & rule maintenance

## Part A — When to create a new skill

Create a skill when **all** of these are true:

1. The procedure has **3+ steps** or a checklist that must be repeated.
2. It will be used **again** (not a one-off task).
3. It needs detail that should not sit in the system prompt (it costs context).
4. No existing skill already covers it — check `.pi/skills/` first and prefer extending an existing skill.

Do **not** create a skill for: a single command, a one-time migration, a task already handled by `agent.md`, or a restatement of framework docs.

## Part B — Procedure

1. **Check first**: list `.pi/skills/`, read names + descriptions, ask "which skill should own this?" If one owns 80% of it, extend that skill instead.
2. **Propose to the owner** one paragraph: name, purpose, why it is needed now. Wait for OK (skills are durable instruction, not scratch notes).
3. **Create the directory**: `.pi/skills/<kebab-name>/SKILL.md`.
4. **Frontmatter** (portable Agent Skills spec):

   ```markdown
   ---
   name: <kebab-name>            # lowercase, digits, hyphens, ≤64 chars
   description: <what it does + WHEN to use it, ≤1024 chars>
   ---
   ```

   The `description` is the routing signal — state **what** and **when**, explicitly ("Use when ...").
5. **Body**: start with the first action, not theory. Use numbered steps, hard gates, and checklists. Include exact `cmd` commands. Keep it under ~150 lines; move details to `references/`.
6. **Supporting files**: `references/` (templates, maps, long tables), `scripts/` (repeatable automation), `assets/`.
7. **Wire it up**: mention the skill where it must trigger (e.g. add a line in `agent.md` §11 pointing to it).
8. **Validate**: run `/reload`, confirm the skill appears and `/skill:<name>` loads it; fix warnings from startup diagnostics.
9. **Record**: add a row to `agent.md` §13 change log and the corresponding `docs/` page.

## Part C — Rules changes always go through `agent.md`

- `agent.md` is the **single source of truth for rules**. Any new/edited rule is written there, in the right section, in the same turn it is agreed.
- Keep the structure: fixed stack (§1), layout (§2), backend (§3), mobile (§4), AI (§5), testing (§6), style (§7), git (§8), docs (§9), process (§10), behaviour (§11), open questions (§12), change log (§13).
- Every edit: update the change log row with a short "what + why", and bump the `Status: rules vN` line.
- If a rule change also affects a skill, update **both** in the same turn — never leave them contradicting.
- If two rules conflict, the newer, more specific one wins, but fix or delete the old one — do not leave contradictions in the file.
- Never weaken a fixed-stack rule silently. Stack changes require explicit owner approval and a changelog entry.
- `AGENTS.md` (root) only points at `agent.md`; it is not a place for rules.
- `PENDING-*` items stay listed until the owner answers; answered items are moved into their section and removed from the list.

## Part D — Keeping skills honest

- Re-read a skill when its area changes; a skill that contradicts the code is a bug.
- Delete skills that no longer apply instead of leaving them half-true.
- One skill = one job. If a skill needs "and also", it is two skills.

---

## Log

| Skill | Created | Purpose |
|---|---|---|
| `github-workflow` | project setup | Branch/issue/PR workflow and merge gates |
| `project-docs` | project setup | Multi-file `docs/` maintenance |
| `skill-authoring` | project setup | Meta: create skills, keep `agent.md` authoritative |
