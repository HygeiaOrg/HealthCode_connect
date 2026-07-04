"""Layer 3: dictionary membership. A code can be perfectly shaped and still not
exist; these checks look terms up in the bundled dictionaries and, when a code
is unknown, suggest the closest valid entry (difflib: deterministic stdlib)."""
from __future__ import annotations

from difflib import SequenceMatcher

from ..engine import Dictionaries, Issue, get_path
from .formats import CCSD_RE, ICD10_RE


def _prefix_len(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def _closest(code: str, pool: list[str]) -> str | None:
    """Closest valid code: shared prefix first (code systems are hierarchical,
    so M17.2 should suggest M17.1, not another .2 code), similarity second,
    alphabetical third. Fully deterministic."""
    scored = [
        (_prefix_len(code, cand), SequenceMatcher(None, code, cand).ratio(), cand)
        for cand in pool
    ]
    scored = [s for s in scored if s[1] >= 0.6]
    if not scored:
        return None
    scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
    return scored[0][2]


def check(invoice: dict, d: Dictionaries) -> list[Issue]:
    issues: list[Issue] = []

    insurer_id = get_path(invoice, "policy.insurer_id")
    if isinstance(insurer_id, str) and insurer_id and insurer_id not in d.insurers:
        hint = _closest(insurer_id, list(d.insurers))
        sol = f"Select a registered insurer. Closest match: {hint} ({d.insurers[hint]['name']})." if hint \
            else "Select the paying insurer from the registered list."
        issues.append(Issue("Insurer", f"'{insurer_id}' is not a registered insurer", sol,
                            rule_id="dict.insurer", path="policy.insurer_id"))

    for i, code in enumerate(get_path(invoice, "episode.diagnoses") or []):
        c = str(code).strip().upper()
        if c and ICD10_RE.match(c) and c not in d.icd10:
            hint = _closest(c, list(d.icd10))
            sol = f"Unknown code. Closest valid: {hint} — {d.icd10[hint]}." if hint \
                else "Pick the diagnosis from the ICD-10 code list."
            issues.append(Issue("Diagnosis Code", f"ICD-10 code '{c}' is not in the code list", sol,
                                rule_id="dict.icd10", path=f"episode.diagnoses[{i}]"))

    for i, code in enumerate(get_path(invoice, "episode.procedures") or []):
        c = str(code).strip().upper()
        if c and CCSD_RE.match(c) and c not in d.ccsd:
            hint = _closest(c, list(d.ccsd))
            sol = f"Unknown code. Closest valid: {hint} — {d.ccsd[hint]['narrative']}." if hint \
                else "Pick the procedure from the loaded CCSD schedule."
            issues.append(Issue("Procedure Code", f"CCSD code '{c}' is not in the loaded schedule", sol,
                                rule_id="dict.ccsd", path=f"episode.procedures[{i}]"))

    for i, line in enumerate(get_path(invoice, "lines") or []):
        sc = line.get("service_code") if isinstance(line, dict) else None
        if isinstance(sc, str) and sc and sc not in d.charge_codes:
            hint = _closest(sc, list(d.charge_codes))
            sol = f"Unmapped charge code. Closest mapped code: {hint} — {d.charge_codes[hint]['description']}." if hint \
                else "Map this charge to an Industry Standard Code before submitting."
            issues.append(Issue("Provider Chargecode", f"Service code '{sc}' is not mapped", sol,
                                rule_id="dict.charge_code", path=f"lines[{i}].service_code"))

    gmc = get_path(invoice, "provider.gmc_number")
    if isinstance(gmc, str) and gmc.strip() and gmc.strip().isdigit() and len(gmc.strip()) == 7 \
            and gmc.strip() not in d.specialists:
        issues.append(Issue("Controlling Specialist", f"No registered specialist with GMC number {gmc}",
                            "Register the specialist on the practice register (Settings) before billing under their name.",
                            rule_id="dict.specialist", path="provider.gmc_number"))

    payee = get_path(invoice, "provider.payee_provider_id")
    if isinstance(payee, str) and payee.strip() and payee not in d.payee_providers:
        issues.append(Issue("Payee Provider", f"'{payee}' is not a recognised payee",
                            "Choose a registered payee provider; payment cannot be routed to an unknown payee.",
                            rule_id="dict.payee", path="provider.payee_provider_id"))

    site = get_path(invoice, "provider.treatment_site_id")
    if isinstance(site, str) and site.strip() and site not in d.treatment_sites:
        issues.append(Issue("Treatment Site", f"'{site}' is not a recognised treatment site",
                            "Choose a registered site; unmapped facilities fail insurer validation.",
                            rule_id="dict.site", path="provider.treatment_site_id"))

    return issues
