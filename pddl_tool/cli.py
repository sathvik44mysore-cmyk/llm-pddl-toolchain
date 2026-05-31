"""
cli.py — Command-line interface for the LLM-PDDL Toolchain.
"""

import sys
import click
from .generator import generate_pddl, repair_pddl
from .solver import solve
from .explainer import explain_plan


@click.command()
@click.argument("task")
@click.option("--show-pddl", is_flag=True, help="Print generated PDDL to stdout.")
@click.option("--no-explain", is_flag=True, help="Skip plain-English explanation.")
@click.option("--timeout", default=30, show_default=True,
              help="Planner timeout in seconds.")
def main(task, show_pddl, no_explain, timeout):
    """
    Solve a planning TASK described in natural language.

    Example:

        pddl-tool "stack block A on block B, then B on C"
    """
    click.echo()

    # ── Step 1: Generate PDDL ───────────────────────────────────────────────
    click.echo(click.style("Generating PDDL...", fg="cyan"), nl=False)
    try:
        domain, problem = generate_pddl(task)
        click.echo(click.style("  done", fg="green"))
    except Exception as e:
        click.echo(click.style(f"  FAILED\n{e}", fg="red"))
        sys.exit(1)

    if show_pddl:
        click.echo("\n── Domain ──────────────────────────────────────────────")
        click.echo(domain)
        click.echo("\n── Problem ─────────────────────────────────────────────")
        click.echo(problem)
        click.echo()

    # ── Step 2: Solve (with one auto-repair attempt) ─────────────────────────
    click.echo(click.style("Solving...     ", fg="cyan"), nl=False)
    result = solve(domain, problem, timeout=timeout)

    if not result["found"]:
        click.echo(click.style("  retrying with repair...", fg="yellow"))
        click.echo(click.style("Repairing PDDL...", fg="cyan"), nl=False)
        try:
            domain, problem = repair_pddl(task, domain, problem, result["error"])
            click.echo(click.style("  done", fg="green"))
            if show_pddl:
                click.echo("\n── Repaired Domain ─────────────────────────────────────")
                click.echo(domain)
                click.echo("\n── Repaired Problem ─────────────────────────────────────")
                click.echo(problem)
                click.echo()
        except Exception as e:
            click.echo(click.style(f"  FAILED ({e})", fg="red"))
            sys.exit(1)

        click.echo(click.style("Solving...     ", fg="cyan"), nl=False)
        result = solve(domain, problem, timeout=timeout)

    if not result["found"]:
        click.echo(click.style("  FAILED", fg="red"))
        click.echo(f"\nError: {result['error']}")
        click.echo("\nTip: try rephrasing the task or use --show-pddl to inspect the generated PDDL.")
        sys.exit(1)

    click.echo(
        click.style("  done", fg="green") +
        f"  ({result['plan_cost']} steps, {result['time_s']:.2f}s)"
    )

    # ── Step 3: Print plan ───────────────────────────────────────────────────
    click.echo()
    click.echo(click.style("Plan:", bold=True))
    for i, action in enumerate(result["plan"], 1):
        click.echo(f"  {i:2}. {action}")

    # ── Step 4: Explain ──────────────────────────────────────────────────────
    if not no_explain:
        click.echo()
        click.echo(click.style("Explanation:", bold=True))
        try:
            explanation = explain_plan(task, result["plan"], domain)
            click.echo(f"  {explanation}")
        except Exception as e:
            click.echo(click.style(f"  (explanation failed: {e})", fg="yellow"))

    click.echo()
