# SPDX-FileCopyrightText: 2020 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import os

from xdg import BaseDirectory

from aportsknife import Package


def find_packages_with_pkgver(pkgver):
    # Make a list of all packages to modify
    packages_to_edit = []
    for root, dirs, files in os.walk(cwd):
        for name in files:
            if name == "APKBUILD":
                filename = os.path.join(root, name)

                # Check if this is a package that we have to modify by
                # verifying the old pkgver is present
                with open(filename, "r") as file_handler:
                    if pkgver in file_handler.read():
                        packages_to_edit.append(Package(cwd, filename))
                        break

    return packages_to_edit


def find_packages(repository):
    # Make a list of all packages in the specified repository
    packages = []
    for root, dirs, files in os.walk(f"{cwd}/{repository}"):
        for name in files:
            if name == "APKBUILD":
                filename = os.path.join(root, name)
                packages.append(Package(cwd, filename))
                break

    return packages


def update_pkgver(pkgver_old, pkgver_new, build=False):
    packages_to_edit = find_packages_with_pkgver(pkgver_old)

    print("Updating pkgvers")
    for package in packages_to_edit:
        package.update_pkgver(pkgver_old, pkgver_new)

    print("Updating checksums")
    for package in packages_to_edit:
        package.update_checksums()

    if build:
        for package in packages_to_edit:
            package.build()


def build_all(repository=None):
    packages = []

    if repository is not None:
        packages += find_packages(repository)
    else:
        for repository in "main", "community", "testing":
            packages += find_packages(repository)

    filename = (BaseDirectory.save_data_path('aportsknife') +
                "/skip_packages.txt")
    packages_to_skip = []
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            for line in f:
                packages_to_skip.append(Package(
                    cwd,
                    f"{cwd}/{line.strip()}/APKBUILD"))

    # Skip packages that are in the skip list
    packages = [i for i in packages if i not in packages_to_skip]

    if packages is not None and len(packages) == 0:
        print("No packages found to build, exiting")
        exit(0)

    for package in packages:
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
