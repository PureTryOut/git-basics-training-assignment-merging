# SPDX-FileCopyrightText: 2022 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import os
from pathlib import Path
from typing import List

import tomlkit
import xdg

from .actions import build, update_pkgver
from .package import Package
from .repository import Repository
from .selectors import (
    find_modified_packages,
    find_packages_with_dep,
    find_packages_with_pkgver,
)


def init() -> None:
    aports_path = Path(os.path.expandvars(input("Path to aports tree: ")))

    if not aports_path.is_dir():
        print("That directory does not exist")

    if aports_path.name != "aports":
        answer = input("This does not seem to be an aports tree, are you sure? [y/N] ")

        if answer != "y":
            exit(0)

    with open(
        xdg.BaseDirectory.save_config_path("aportsknife") + "/config.toml",
        "w",
        encoding="utf-8",
    ) as file:
        toml_document = tomlkit.document()
        toml_table_general = tomlkit.table()
        toml_table_general.add("aports_path", str(aports_path))
        toml_document.add("general", toml_table_general)
        tomlkit.dump(toml_document, fp=file)


def get_duplicates_in_lists(list1: [Repository], list2: [Repository]) -> [Repository]:
    packages_list1 = []
    packages_list2 = []

    repository: Repository
    for repository in list1:
        packages_list1 += repository.packages

    for repository in list2:
        packages_list2 += repository.packages

    duplicate_packages = set(packages_list1) & set(packages_list2)

    repositories = []

    package: Package
    for package in duplicate_packages:
        if package.repository not in repositories:
            repositories.append(Repository(package.repository.path, []))

        repository: Repository = repositories[repositories.index(package.repository)]
        repository.packages.append(package)

    return repositories


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
    parser.add_argument(
        "--select-with-dep",
        type=str,
        help="Select packages with this dependency (globbed, e.g. 'qt5-qtbase' will also find packages with 'qt5-qtbase-dev'",
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

    if not Path(xdg.BaseDirectory.save_config_path("aportsknife") + "/config.toml").is_file() and (
        args.action is None or args.action != "init"
    ):
        print("Please run aportsknife init first")
        exit(0)

    if args.action is not None and args.action == "init":
        init()
        exit(0)

    selectors_used = False
    actions_used = False
    if not all(val is None for val in [args.select_version, args.select_with_dep]) or args.select_changed is not False:
        selectors_used = True

    if args.set_version is not None or args.build is not False:
        actions_used = True

    if selectors_used is False:
        print("You need to select some packages to operate on")
        print("Run aportsknife -h for usage information")
        exit(1)
    if actions_used is False:
        print("WARNING: No action has been specified")

    # Select packages
    print("Finding packages...")

    found_packages_by_selectors = {}
    if args.select_version is not None:
        found_packages_in_repositories = find_packages_with_pkgver(args.select_version)

        found_packages_by_selectors["select_version"] = found_packages_in_repositories

    if args.select_changed is not False:
        found_packages_in_repositories = find_modified_packages()

        found_packages_by_selectors["select_changed"] = found_packages_in_repositories

    if args.select_with_dep is not None:
        found_packages_in_repositories = find_packages_with_dep(args.select_with_dep)

        found_packages_by_selectors["select_with_dep"] = found_packages_in_repositories

    # Combine all packages found by the selectors into a single list with the duplicates between them
    # That way we only get packages that have been found by all selectors
    repositories: List[Repository] = []
    i = 0
    for key in found_packages_by_selectors:
        if i == 0:
            repositories = found_packages_by_selectors[key]
        else:
            repositories = get_duplicates_in_lists(repositories, found_packages_by_selectors[key])

        i += 1

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
