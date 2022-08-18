# SPDX-FileCopyrightText: 2020 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import os
from pathlib import Path
from typing import List

import xdg
import yaml

from .actions import build, update_pkgver
from .selectors import find_modified_packages, find_packages_with_pkgver


def init() -> None:
    aports_path = Path(os.path.expandvars(input("Path to aports tree: ")))

    if not aports_path.is_dir():
        print("That directory does not exist")

    if aports_path.name != "aports":
        answer = input("This does not seem to be an aports tree, are you sure? [y/N] ")

        if answer != "y":
            exit(0)

    with open(xdg.BaseDirectory.save_config_path("aportsknife") + "/config.yaml", "w") as file:
        yaml.dump({"aports_path": str(aports_path)}, file)


def main():
    parser = argparse.ArgumentParser(
        prog="aportsknife",
        description="Swiss army knife for bulk aports operations.",
    )

    sub = parser.add_subparsers(title="action", dest="action")

    # Init command
    sub.add_parser("init", help="initialize aportsknife")

    # We work with "selectors" and "actions"
    # The user has to "select" packages by specifying certain filters.
    # This can be packages with a specific version, every package that has changed according to git, etc
    # Once the selectors have been set, the user can specify what actions to execute on them
    # This can for example be changing the pkgver to a new one, or build them all in the right order

    # Package selectors
    parser.add_argument(
        "--select-version",
        type=str,
        help="Select packages with this version",
    )
    parser.add_argument(
        "--select-changed",
        action="store_true",
        help="Select packages changed in the current git branch",
    )

    # Package actions
    parser.add_argument(
        "--set-version",
        type=str,
        help="Set the selected packages to the specified version",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build the selected packages",
    )

    args = parser.parse_args()

    if not Path(xdg.BaseDirectory.save_config_path("aportsknife") + "/config.yaml").is_file() and (
        args.action is None or args.action != "init"
    ):
        print("Please run aportsknife init first")
        exit(0)

    if args.action is not None and args.action == "init":
        init()
        exit(0)

    selectors_used = False
    actions_used = False
    if args.select_version is not None or args.select_changed is not False:
        selectors_used = True

    if args.set_version is not None or args.build is not False:
        actions_used = True

    if selectors_used is False:
        print("You need to select some packages to operate on")
        print("Run aportsknife -h for usage information")
        exit(1)
    elif actions_used is False:
        print("You need to specify an action to execute on the selected packages")
        print("Run aportsknife -h for usage information")
        exit(1)

    def combine_repository_lists(list1, list2):
        for found_repository in list2:
            if found_repository not in list1:
                list1.append(found_repository)
            else:
                repository = list1[list1.index(found_repository)]
                for package in found_repository.packages:
                    if package not in repository.packages:
                        repository.packages.append(package)

    # Select packages
    print("Finding packages...")

    repositories: List[Repository] = []
    if args.select_version is not None:
        found_packages_in_repositories = find_packages_with_pkgver(args.version)

        combine_repository_lists(repositories, found_packages_in_repositories)

    if args.select_changed is not None:
        found_packages_in_repositories = find_modified_packages()

        combine_repository_lists(repositories, found_packages_in_repositories)

    found_package_count = 0
    for repository in repositories:
        found_package_count += len(repository.packages)

    if found_package_count == 0:
        print("No packages found with the specified selector(s)!")
        exit(0)

    print(f"Found {found_package_count} package(s)")

    # Execute actions on found packages
    if args.set_version is not None:
        print(f"Changing package versions to {args.set_version}...")
        update_pkgver(repositories=repositories, pkgver=args.set_version)

    if args.build is not False:
        print("Building packages...")
        build(repositories)
