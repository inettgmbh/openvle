"""
Seed fixture data into the database for testing, staging, or demo.
"""

import argparse
import logging
import sys

_USAGE = """\
python -m scripts.seed_fixtures -p <profile> [options]

OpenVLE Fixture Seeder

Profiles:
  testing   Minimal data for CI/integration tests
  staging   Moderate data for staging/QA
  demo      Realistic data for demos (~750 users)

Options:
  -p, --profile   Profile to seed (required)
  --purge         Delete fixture data before seeding
  --purge-only    Only delete, do not re-seed
  --dry-run       Roll back after generating
  -v, --verbose   Debug logging

Examples:
  python -m scripts.seed_fixtures -p demo
  python -m scripts.seed_fixtures -p demo --purge
  python -m scripts.seed_fixtures -p testing --dry-run
  python -m scripts.seed_fixtures -p staging --purge-only"""


def main() -> None:
    parser = argparse.ArgumentParser(usage=_USAGE, add_help=False)
    parser.add_argument(
        "--profile", "-p", choices=["testing", "staging", "demo"]
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--purge", action="store_true")
    parser.add_argument("--purge-only", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--help", "-h", action="store_true")

    args = parser.parse_args()

    if args.help or not args.profile:
        print(f"usage: {_USAGE}")
        sys.exit(0 if args.help else 1)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[seed] %(levelname)s %(message)s",
    )

    from fixtures.constants import Profile
    from fixtures.runner import purge, seed

    profile = Profile(args.profile)

    if args.purge or args.purge_only:
        purge(profile)

    if not args.purge_only:
        seed(profile, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[seed] Failed: {e}", file=sys.stderr)
        sys.exit(1)
