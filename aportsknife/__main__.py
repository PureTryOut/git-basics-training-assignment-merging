# SPDX-FileCopyrightText: 2020 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import os
from pathlib import Path

import git

from aportsknife import Package, Repository


def find_repositories() -> [Repository]:
    repositories = []
    for directory in [x for x in Path(cwd).iterdir() if x.is_dir()]:
        if len(directory.name.split(".")) > 1:
            continue

        is_repository = [] != [
            x
            for x in directory.iterdir()
            if x.is_file() and x.name == ".rootbld-repositories"
        ]

        if not is_repository:
            continue

        repositories.append(Repository(directory, []))

    return repositories


def find_packages_with_pkgver(pkgver) -> [Repository]:
    # Make a list of all repositories
    repositories = find_repositories()
    for repository in repositories:
        # Make a list of all packages to update
        for package in [x for x in repository.path.iterdir() if x.is_dir()]:
            apkbuild = [
                x
                for x in package.glob("**/*")
                if x.is_file() and x.name == "APKBUILD"
            ]
            if len(apkbuild) < 1:
                continue

            apkbuild = apkbuild[0]

            with apkbuild.open() as file_handler:
                if pkgver in file_handler.read():
                    # TODO: fix that CWD thing
                    repository.packages.append(Package(cwd, str(apkbuild)))

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


def find_modified_packages() -> [Repository]:
    repositories = find_repositories()
    repo = git.Repo(cwd)

    # Get committed and staged files
    changed_files = [
        x for x in repo.index.diff("master") if "APKBUILD" in x.a_path
    ]

    # Get unstaged files
    changed_files += [
        x for x in repo.index.diff(None) if "APKBUILD" in x.a_path
    ]
    for changed_file in changed_files:
        for repository in repositories:
            if repository.name in changed_file.a_path:
                repository.packages.append(
                    Package(cwd, f"{cwd}/" + str(changed_file.a_path))
                )

    for repository in repositories:
        repository.sort()

    return repositories


def build_branch():
    repositories = find_modified_packages()
    for repository in repositories:
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
        description="Swiss army knife for bulk aports operations.",
    )
    sub = parser.add_subparsers(title="action", dest="action")
    update = sub.add_parser("update", help="update pkgver in bulk")
    update.add_argument("pkgver_old", help="the pkgver to update from")
    update.add_argument("pkgver_new", help="the pkgver to update to")
    update.add_argument(
        "-b",
        "--build",
        action="store_true",
        help="Also build the updated packages",
    )

    sub.add_parser("build", help="build all updated packages in this branch")

    args = parser.parse_args()

    if args.action:
        if args.action == "update":
            update_pkgver(args.pkgver_old, args.pkgver_new, args.build)
        elif args.action == "build":
            build_branch()

    else:
        print("Run aportsknife -h for usage information")


if __name__ == "__main__":
    main()
