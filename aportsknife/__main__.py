# SPDX-FileCopyrightText: 2020 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path

import git
import xdg
import yaml

from aportsknife import Package, Repository, Settings


def init() -> None:
    aports_path = Path(os.path.expandvars(input("Path to aports tree: ")))

    if not aports_path.is_dir():
        print("That directory does not exist")

    if aports_path.name != "aports":
        answer = input(
            "This does not seem to be an aports tree, are you sure? [y/N] "
        )

        if answer != "y":
            exit(0)

    with open(
        xdg.BaseDirectory.save_config_path("aportsknife") + "/config.yaml", "w"
    ) as file:
        yaml.dump({"aports_path": str(aports_path)}, file)


def find_repositories() -> [Repository]:
    settings = Settings()
    repositories = []
    for directory in [x for x in settings.aports_path.iterdir() if x.is_dir()]:
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

            with open(apkbuild) as source:
                for line in source:
                    if "pkgver=" in line:
                        # Example: "pkgver=5.12.3\n"
                        # So split by =, take only the version and remove the
                        # new line
                        apkbuild_pkgver = line.split("=")[1].removesuffix("\n")
                        if apkbuild_pkgver == pkgver:
                            repository.packages.append(
                                Package(
                                    repository, str(apkbuild).split("/")[-2]
                                )
                            )

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
    settings = Settings()

    repositories = find_repositories()
    repo = git.Repo(settings.aports_path)

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
                    Package(
                        repository,
                        str(changed_file.a_path.split("/")[-2]),
                    )
                )

    for repository in repositories:
        repository.sort()

    return repositories


def build_branch():
    repositories = find_modified_packages()
    for repository in repositories:
        for package in repository.packages:
            package.build()