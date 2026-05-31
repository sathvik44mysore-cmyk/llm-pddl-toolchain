"""
run_benchmarks.py — Run Fast Downward against hand-written PDDL problems.

Usage:
    python benchmarks/run_benchmarks.py

For each domain subdirectory under benchmarks/problems/, load the matching
domain PDDL from domains/ and solve every .pddl problem file.  Results are
printed to stdout and returned as a list of dicts for the API to persist.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pddl_tool.solver import solve

DOMAINS_DIR   = os.path.join(os.path.dirname(__file__), "..", "domains")
PROBLEMS_DIR  = os.path.join(os.path.dirname(__file__), "problems")


def run_benchmarks() -> list[dict]:
    results = []

    if not os.path.isdir(PROBLEMS_DIR):
        print("No benchmark problems directory found.")
        return results

    domain_dirs = sorted(
        d for d in os.listdir(PROBLEMS_DIR)
        if os.path.isdir(os.path.join(PROBLEMS_DIR, d))
    )

    for domain_name in domain_dirs:
        domain_path = os.path.join(DOMAINS_DIR, f"{domain_name}.pddl")
        if not os.path.exists(domain_path):
            print(f"  [skip] No domain file for '{domain_name}'")
            continue

        with open(domain_path) as f:
            domain_pddl = f.read()

        problem_dir = os.path.join(PROBLEMS_DIR, domain_name)
        problem_files = sorted(
            p for p in os.listdir(problem_dir) if p.endswith(".pddl")
        )

        if not problem_files:
            continue

        print(f"\n{domain_name}:")
        for pf in problem_files:
            problem_name = pf[:-5]
            problem_path = os.path.join(problem_dir, pf)
            with open(problem_path) as f:
                problem_pddl = f.read()

            result = solve(domain_pddl, problem_pddl, timeout=60)
            status = "✓" if result["found"] else "✗"
            print(
                f"  {status} {problem_name}: "
                f"{result['plan_cost']} steps, {result['time_s']:.2f}s"
                + (f"  [{result['error']}]" if not result["found"] else "")
            )

            results.append({
                "domain_name": domain_name,
                "problem_name": problem_name,
                "found": result["found"],
                "plan_cost": result["plan_cost"] if result["found"] else None,
                "solve_time_s": round(result["time_s"], 3),
            })

    return results


if __name__ == "__main__":
    print("Running PlanForge benchmarks...\n")
    results = run_benchmarks()
    total   = len(results)
    found   = sum(1 for r in results if r["found"])
    print(f"\n{'='*40}")
    print(f"Results: {found}/{total} plans found ({round(found/total*100) if total else 0}%)")
