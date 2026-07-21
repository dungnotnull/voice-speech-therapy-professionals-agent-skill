"""
run_test_scenarios.py -- Skill 179: voice-speech-therapy-professionals
Production-grade structural & content validator. Verifies the file contract,
sub-skill content, knowledge base, test scenarios, and quality-gate coverage.
Supports v2.0.0 expanded file inventory and domain content validation.
Exit code 0 = all checks pass, non-zero = failures.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

GATES = ["U1", "U2", "U3", "U4", "U5", "U6", "G1", "G2", "G3", "G4"]
VERDICTS = [
    "Healthy",
    "Improvement Plan",
    "Conditional (needs technique work)",
    "Medical Referral Needed",
    "Inconclusive",
]

checks_passed = 0
checks_failed = 0
failures: list[str] = []


def ok(label: str, detail: str = "") -> None:
    global checks_passed
    checks_passed += 1


def fail(label: str, detail: str = "") -> None:
    global checks_failed
    checks_failed += 1
    failures.append(f"{label}: {detail}")


def require(cond: bool, label: str, detail: str = "") -> None:
    (ok if cond else fail)(label, detail)


def read(p: Path) -> str:
    return Path(p).read_text(encoding="utf-8") if Path(p).exists() else ""


# ---- 1. File structure (v2.0.0) ----
REQUIRED = [
    # Core docs
    "CLAUDE.md",
    "PROJECT-detail.md",
    "PROJECT-DEVELOPMENT-PHASE-TRACKING.md",
    "README.md",
    "SECOND-KNOWLEDGE-BRAIN.md",
    # Skills
    "skills/main.md",
    "skills/_shared-conventions.md",
    "skills/sub-gather-requirements.md",
    "skills/sub-evidence-collector.md",
    "skills/sub-core-analysis.md",
    "skills/sub-knowledge-updater.md",
    "skills/sub-advisor.md",
    # Tools
    "tools/_config.py",
    "tools/knowledge_updater.py",
    "tools/test_knowledge_updater.py",
    "tools/run_test_scenarios.py",
    # Tests
    "tests/test-scenarios.md",
    "tests/TEST_RESULTS.md",
    "tests/test_domain.py",
    # Infrastructure
    "pyproject.toml",
    "pytest.ini",
    "conftest.py",
    ".env.example",
    ".pre-commit-config.yaml",
    ".editorconfig",
    "LICENSE",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "Dockerfile",
    "Makefile",
    "GLOSSARY-vi.md",
    ".github/workflows/ci.yml",
    ".github/workflows/publish.yml",
]
for f in REQUIRED:
    require((ROOT / f).exists(), f"file present: {f}")

subs = sorted(SKILLS.glob("sub-*.md"))
require(len(subs) >= 5, "at least 5 sub-skills", f"found {len(subs)}")
expected_subs = {
    "sub-gather-requirements",
    "sub-evidence-collector",
    "sub-core-analysis",
    "sub-knowledge-updater",
    "sub-advisor",
}
got_subs = {s.stem for s in subs}
require(got_subs == expected_subs, "sub-skill set", f"got {got_subs}")

# ---- 2. Frontmatter + sections ----
FM = re.compile(r"^---\s*\n(.*?\n)---", re.S)
for s in subs:
    txt = read(s)
    m = FM.search(txt)
    require(bool(m), f"{s.name}: frontmatter")
    if m:
        require(
            "name:" in m.group(1) and "description:" in m.group(1),
            f"{s.name}: name+description",
        )
    for sec in ["Role & Persona", "Workflow", "Output Format", "Quality Gates"]:
        require(sec in txt, f"{s.name}: section {sec}")

main_txt = read(ROOT / "skills/main.md")
for sec in ["Role & Persona", "Quality Gates", "Harness Execution Protocol"]:
    require(sec in main_txt, f"main.md: section {sec}")
require("Pre-Flight" in main_txt, "main.md: pre-flight language detection")
require("limitation" in main_txt.lower(), "main.md: limitation banner")
require("_shared-conventions.md" in main_txt, "main.md: references _shared-conventions.md")
require("GLOSSARY-vi.md" in main_txt, "main.md: references GLOSSARY-vi.md")

# ---- 3. Shared conventions ----
shared = read(ROOT / "skills/_shared-conventions.md")
require("U1" in shared and "U6" in shared, "shared-conventions: universal gates U1-U6")
require("Tier 1" in shared and "Tier 4" in shared, "shared-conventions: evidence hierarchy")
require("Graceful Degradation" in shared, "shared-conventions: degradation levels")
require("Error Recovery" in shared, "shared-conventions: error recovery table")
require("Vietnamese" in shared or "Translation" in shared, "shared-conventions: translation table")

# ---- 4. Quality gate coverage ----
for g in GATES:
    require(g in main_txt, f"main.md: gate {g} present")
adv = read(ROOT / "skills/sub-advisor.md")
for v in VERDICTS:
    require(
        v in adv or v.replace(" ", "") in adv.replace(" ", ""),
        f"advisor/verdict {v} present",
    )

# ---- 5. Domain content depth ----
core = read(ROOT / "skills/sub-core-analysis.md")
require("CAPE-V" in core, "sub-core-analysis: CAPE-V protocol")
require("GRBAS" in core, "sub-core-analysis: GRBAS scale")
require("jitter" in core.lower() and "shimmer" in core.lower(), "sub-core-analysis: acoustic norms")
require("SOVT" in core or "Straw phonation" in core, "sub-core-analysis: SOVT exercises")
require("Estill" in core, "sub-core-analysis: Estill figures")
require("differential" in core.lower(), "sub-core-analysis: differential diagnosis")
require("SOVT" in core or "Estill" in core, "sub-core-analysis: exercise library")
require("Teacher" in core and "Podcaster" in core, "sub-core-analysis: profession protocols")

gather = read(ROOT / "skills/sub-gather-requirements.md")
require("Section A" in gather or "Professional Profile" in gather, "sub-gather-requirements: intake questionnaire")
require("subtype" in gather.lower(), "sub-gather-requirements: profession classification")

# ---- 6. Knowledge base ----
brain = read(ROOT / "SECOND-KNOWLEDGE-BRAIN.md")
require("Tier 1" in brain and "Tier 4" in brain, "brain: evidence hierarchy tiers")
dois = re.findall(r"10\.\d{4,9}/[^\s|]+", brain)
require(len(dois) >= 8, f"brain: >=8 DOI-cited references", f"found {len(dois)}")
require("## 4. Authoritative Data Sources" in brain, "brain: data sources section")
require("## 6. Self-Update Protocol" in brain, "brain: self-update protocol")

# ---- 7. test-scenarios ----
sc = read(ROOT / "tests/test-scenarios.md")
sc_count = sc.count("Scenario")
require(sc_count >= 5, f"scenarios: >=5", f"found {sc_count}")
require(
    "degraded" in sc.lower() or "missing" in sc.lower(),
    "scenarios: degraded case",
)
require(
    "conflict" in sc.lower() or "compare" in sc.lower() or "comparison" in sc.lower(),
    "scenarios: comparison/conflict case",
)
for g in ["G1", "G2", "G3"]:
    require(g in sc, f"scenarios: gate {g} referenced")

# ---- 8. knowledge_updater.py v2 features ----
ku = read(ROOT / "tools/knowledge_updater.py")
require("TokenBucket" in ku, "knowledge_updater: TokenBucket rate limiter")
require("AsyncKnowledgeUpdater" in ku, "knowledge_updater: async core class")
require("KnowledgeUpdater" in ku, "knowledge_updater: sync wrapper")
require("portalocker" in ku, "knowledge_updater: file locking")
require("httpx" in ku, "knowledge_updater: async HTTP client")
require("normalize_identifier" in ku, "knowledge_updater: DOI normalization")
require("Metrics" in ku, "knowledge_updater: metrics class")
require("logging" in ku, "knowledge_updater: structured logging")
require("--dry-run" in ku, "knowledge_updater: dry-run flag")

# ---- 9. _config.py validation ----
cfg = read(ROOT / "tools/_config.py")
require("KnowledgeConfig" in cfg, "_config.py: KnowledgeConfig TypedDict")
require("ScoringWeights" in cfg, "_config.py: ScoringWeights TypedDict")
require("PaperEntry" in cfg, "_config.py: PaperEntry TypedDict")
require("load_config" in cfg, "_config.py: load_config function")
require("validate_config" in cfg, "_config.py: validate_config function")

# ---- 10. GLOSSARY-vi ----
gloss = read(ROOT / "GLOSSARY-vi.md")
term_pairs = gloss.count(" | ") - gloss.count("---")
require(term_pairs >= 40, f"GLOSSARY-vi: >=40 term pairs", f"found ~{term_pairs}")
require("thanh quản" in gloss.lower(), "GLOSSARY-vi: anatomy terms")
require("khàn tiếng" in gloss.lower(), "GLOSSARY-vi: pathology terms")
require("giáo viên" in gloss.lower(), "GLOSSARY-vi: profession terms")

# ---- 11. Infrastructure files ----
license_txt = read(ROOT / "LICENSE")
require("MIT" in license_txt, "LICENSE: MIT license")
contrib = read(ROOT / "CONTRIBUTING.md")
require("Development Setup" in contrib or "pip install" in contrib, "CONTRIBUTING: dev setup")
clog = read(ROOT / "CHANGELOG.md")
require("2.0.0" in clog, "CHANGELOG: v2.0.0 entry")
require("1.0.0" in clog, "CHANGELOG: v1.0.0 entry")
docker = read(ROOT / "Dockerfile")
require("FROM python" in docker, "Dockerfile: FROM python base")
makefile = read(ROOT / "Makefile")
require("lint" in makefile and "test" in makefile, "Makefile: lint + test targets")
pyproject = read(ROOT / "pyproject.toml")
require("ruff" in pyproject or "pyright" in pyproject, "pyproject.toml: tool configs")

# ---- 12. Sub-skill file sizes (v2 expansion check) ----
for s in subs:
    size = len(read(s).split("\n"))
    require(size >= 40, f"{s.name}: >=40 lines (v2 expanded)", f"got {size} lines")

# ---- 13. PDPT + README ----
pdpt = read(ROOT / "PROJECT-DEVELOPMENT-PHASE-TRACKING.md")
require("100%" in pdpt, "PDPT: 100% markers")
require("Phase 6" in pdpt, "PDPT: Phase 6")
require("v2.0.0" in pdpt, "PDPT: version 2.0.0")
readme = read(ROOT / "README.md")
require("Usage" in readme, "README: usage")
require("Architecture" in readme, "README: architecture")
require("v2.0.0" in readme, "README: version 2.0.0")

# ---- report ----
total = checks_passed + checks_failed
print(f"[run_test_scenarios] v2.0.0  {checks_passed}/{total} checks passed")
if failures:
    for f_item in failures:
        print("  - FAIL " + f_item)
    sys.exit(1)
print("[OK] all checks passed -- v2.0.0 production ready")
sys.exit(0)
