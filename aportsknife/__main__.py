# SPDX-FileCopyrightText: 2020 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import os
from pathlib import Path

from aportsknife import Package, Repository


def find_packages_with_pkgver(pkgver) -> [Repository]:
    # Make a list of all repositories
    repositories = []
    for directory in [x for x in Path(cwd).iterdir() if x.is_dir()]:
        if len(directory.name.split(".")) > 1:
            continue

        is_repository = [] != [x for x in directory.iterdir() if x.is_file()
                               and x.name == ".rootbld-repositories"]

        if not is_repository:
            continue

        repository = Repository(directory, [])

        # Make a list of all packages to update
        for package in [x for x in directory.iterdir() if x.is_dir()]:
            apkbuild = [x for x in package.glob("**/*") if x.is_file()
                        and x.name == "APKBUILD"]
            if len(apkbuild) < 1:
                continue

            apkbuild = apkbuild[0]

            with apkbuild.open() as file_handler:
                if pkgver in file_handler.read():
                    # TODO: fix that CWD thing
                    repository.packages.append(Package(
                        cwd,
                        str(apkbuild)))

        repositories.append(repository)

    return repositories


def update_pkgver(pkgver_old, pkgver_new, build=False):
    repositories = find_packages_with_pkgver(pkgver_old)

    for repository in repositories:
        repository.update_packages_pkgver(pkgver_old, pkgver_new)

    print("\n")

    if build:
        for repository in repositories:
            repository.sort()

            for package in repository.packages:
                package.build()


def main():
    # We have to check if the current working directory contains "aports" and
    # we're actually in an aports tree
    global cwd
    cwd = os.getcwd()
    if os.path.basename(cwd) != "aports":
        print("This script only works from the root of the aports tree!")
        exit(1)

    parser = argparse.ArgumentParser(
            prog="aportsknife",
            description="Swiss army knife for bulk aports operations.")
    sub = parser.add_subparsers(title="action", dest="action")
    update = sub.add_parser("update", help="update pkgver in bulk")
    update.add_argument("pkgver_old")
    update.add_argument("pkgver_new")
    update.add_argument(
            "-b", "--build",
            action="store_true",
            help="Also build the updated packages")

    args = parser.parse_args()

    if args.action:
        if args.action == "update":
            update_pkgver(args.pkgver_old, args.pkgver_new, args.build)

    else:
        print("Run aportsknife -h for usage information")


if __name__ == '__main__':
    main()
