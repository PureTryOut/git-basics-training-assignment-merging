# SPDX-FileCopyrightText: 2020 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

from .package import Package
from .repository import Repository
from .settings import Settings

import argparse

def main():
    parser = argparse.ArgumentParser(
        prog="aportsknife",
        description="Swiss army knife for bulk aports operations.",
    )
    sub = parser.add_subparsers(title="action", dest="action")

    # Init command
    sub.add_parser("init", help="initialize aportsknife")

    # Update command
    update = sub.add_parser("update", help="update pkgver in bulk")
    update.add_argument("pkgver_old", help="the pkgver to update from")
    update.add_argument("pkgver_new", help="the pkgver to update to")
    update.add_argument(
        "-b",
        "--build",
        action="store_true",
        help="Also build the updated packages",
    )

    # Build command
    sub.add_parser("build", help="build all updated packages in this branch")

    args = parser.parse_args()

    if args.action:
        if (
            args.action != "init"
            and not Path(
                xdg.BaseDirectory.save_config_path("aportsknife")
                + "/config.yaml"
            ).is_file()
        ):
            print("Please run aportsknife init first")
            exit(0)

        if args.action == "init":
            init()
        elif args.action == "update":
            update_pkgver(args.pkgver_old, args.pkgver_new, args.build)
        elif args.action == "build":
            build_branch()

    else:
        print("Run aportsknife -h for usage information")