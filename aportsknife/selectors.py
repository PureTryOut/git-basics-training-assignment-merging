# SPDX-FileCopyrightText: 2022 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import git

from .package import Package
from .repository import Repository
from .settings import Settings


def find_repositories() -> [Repository]:
    settings = Settings()
    repositories = []
    for directory in [x for x in settings.aports_path.iterdir() if x.is_dir()]:
        if len(directory.name.split(".")) > 1:
            continue

        is_repository = [] != [x for x in directory.iterdir() if x.is_file() and x.name == ".rootbld-repositories"]

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
            apkbuild = [x for x in package.glob("**/*") if x.is_file() and x.name == "APKBUILD"]
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
                            repository.packages.append(Package(repository, str(apkbuild).split("/")[-2]))

    return repositories


def find_modified_packages() -> [Repository]:
    settings = Settings()

    repositories = find_repositories()
    repo = git.Repo(settings.aports_path)

    # Get committed and staged files
    changed_files = [x for x in repo.index.diff("master") if "APKBUILD" in x.a_path]

    # Get unstaged files
    changed_files += [x for x in repo.index.diff(None) if "APKBUILD" in x.a_path]
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


def find_packages_with_dep(dep_glob) -> [Repository]:
    repositories = find_repositories()
    for repository in repositories:
        # Make a list of all packages to update
        for package in [x for x in repository.path.iterdir() if x.is_dir()]:
            apkbuild = [x for x in package.glob("**/*") if x.is_file() and x.name == "APKBUILD"]
            if len(apkbuild) < 1:
                continue

            apkbuild = apkbuild[0]

            with open(apkbuild) as source:
                in_deps = False
                lines_with_deps = []
                for line in source:
                    if (
                        not in_deps
                        and "depends=" in line
                        or "makedepends=" in line
                        or "depends_dev" in line
                        or "checkdepends=" in line
                    ):
                        in_deps = True
                        lines_with_deps.append(line)
                    elif in_deps:
                        lines_with_deps.append(line)
                        if '"' in line:
                            in_deps = False

                if len(lines_with_deps) > 0:
                    for line in lines_with_deps:
                        if dep_glob in line:
                            package = Package(repository, str(apkbuild).split("/")[-2])
                            repository.packages.append(package)
                            break

    return repositories
