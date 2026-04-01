# 🤝 Contributing to Skill OS

*Welcome to the revolution. Here's how to join it.*

We're building the operating system for human‑aligned intelligence — and we need builders, thinkers, writers, and critics to do it well. Every contribution matters.

---

## 📋 Before You Begin

1. Read the [README.md](README.md) — understand the mission.
2. Read the [MANIFESTO.md](MANIFESTO.md) — understand the principles.
3. Read the [Code of Conduct](CODE_OF_CONDUCT.md) — understand the culture.
4. Browse the [SKILL_REGISTRY.json](SKILL_REGISTRY.json) — understand what exists.

---

## 🌱 Ways to Contribute

### **Design a new skill**
The most impactful contribution. Add a new atomic, molecular, system, or meta skill.

### **Improve an existing skill**
Sharpen a spec, fix an ambiguity, add examples, improve the contract.

### **Write documentation**
Clarity is a skill. Help others understand the system.

### **Report a governance issue**
Found a skill that violates safety principles? That's a critical contribution.

### **Propose architecture changes**
Open a discussion. We build in public.

### **Review pull requests**
Code review is care. Skill review is craft.

---

## 🛠 How to Add a New Skill

### Step 1 — Check the registry
Search `SKILL_REGISTRY.json` to confirm your skill doesn't already exist.

### Step 2 — Choose the right level

| Level | Use when… |
|-------|-----------|
| **L1 Atomic** | Single, pure operation. No side effects. Deterministic. |
| **L2 Molecular** | Combines 2+ atomic skills. Multi-step. Purpose-driven. |
| **L3 System** | Agentic workflow. Multi-tool. Stateful. |
| **L4 Meta** | Governs, evaluates, or reflects on other skills. |

### Step 3 — Use the skill template
See `docs/skill-design-guide.md` for the full spec template.

Every skill requires:
- `name` — unique, snake_case identifier
- `level` — L1 / L2 / L3 / L4
- `domain` — from the approved domain list
- `description` — one sentence, precise
- `inputs` — typed input schema
- `outputs` — typed output schema
- `contract` — what it will and will not do
- `governance` — approval requirements, if any

### Step 4 — Add to the registry
Add your skill entry to `SKILL_REGISTRY.json`.

### Step 5 — Open a pull request
Use the PR template. Fill it out completely.

---

## 📐 Skill Quality Standards

A skill is ready to merge when:

- [ ] It has a complete, unambiguous spec
- [ ] Inputs and outputs are fully typed
- [ ] The contract explicitly states what it will NOT do
- [ ] Governance requirements are documented
- [ ] It has at least one worked example
- [ ] It does not duplicate an existing skill
- [ ] The registry entry is valid JSON

---

## 🔀 Pull Request Process

1. **Fork** the repository
2. **Create a branch** — use `skill/your-skill-name` or `docs/your-change`
3. **Make your changes**
4. **Run validation** (see `docs/how-to-add-a-skill.md` for tooling)
5. **Open a PR** — fill out the template fully
6. **Respond to review** — discussion is part of the process
7. **Merge** — maintainers merge after approval

---

## n8n Endpoint Config Rules

All n8n HTTP endpoints are defined in `config/n8n_endpoints.json`. Each endpoint must include:

- `category`: one of:
  - `content_automation` — posting, captioning, scheduling, or any content workflow
  - `infra_sensitive` — operations that touch infra, secrets, or data pipelines
  - `reporting` — analytics, dashboards, or metrics-only flows

The test suite enforces this and will fail CI if any endpoint uses another value.

### When adding or editing endpoints

1. Update `config/n8n_endpoints.json` with the new endpoint.
2. Choose a valid `category` from the list above.
3. Run the targeted test locally before pushing:

   ```bash
   ./scripts/check_n8n_endpoints.sh
   ```

4. Only open a PR once this passes.

If you truly need a new category, update the allowed set in `tests/test_n8n.py` in the same PR and document the rationale in the change-request doc.

---

## 🚫 What We Don't Accept

- Skills with no governance contract
- Skills designed for deception or harm
- Duplicates without clear differentiation
- Breaking changes without discussion
- PRs that skip the template

---

## 💬 Where to Discuss

- **GitHub Issues** — proposals, bugs, governance questions
- **GitHub Discussions** — architecture, philosophy, ideas
- **Pull Requests** — specific skill reviews

---

## 🙏 Recognition

Every merged contributor is listed in the registry attribution.
Every skill carries the name of its author.
Governance contributions are highlighted — they protect the whole system.

---

*This is a community of builders who believe intelligence should be transparent.*
*Your contribution makes that belief real.*
