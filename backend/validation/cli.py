"""CLI: python -m validation path/to/invoice.json [--json]

Exit code 0 when no blocking errors (warnings allowed), 1 otherwise."""
from __future__ import annotations

import argparse
import json
import sys

from .engine import is_valid, validate_invoice


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validation", description="Validate a UK private medical invoice.")
    parser.add_argument("invoice", help="Path to an invoice JSON file")
    parser.add_argument("--json", action="store_true", help="Emit issues as JSON")
    args = parser.parse_args(argv)

    with open(args.invoice) as f:
        invoice = json.load(f)

    issues = validate_invoice(invoice)

    if args.json:
        print(json.dumps({
            "valid": is_valid(issues),
            "issues": [{**i.to_contract(), "severity": i.severity, "rule": i.rule_id, "path": i.path} for i in issues],
        }, indent=2))
    elif not issues:
        print("Valid: no issues found.")
    else:
        for i in issues:
            flag = "ERROR  " if i.severity == "error" else "WARNING"
            print(f"[{flag}] {i.field}: {i.error}")
            print(f"          fix: {i.solution}")
        errors = sum(1 for i in issues if i.severity == "error")
        print(f"\n{errors} error(s), {len(issues) - errors} warning(s).")

    return 0 if is_valid(issues) else 1


if __name__ == "__main__":
    sys.exit(main())
