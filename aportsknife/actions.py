# SPDX-FileCopyrightText: 2022 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path
from typing import List

from .repository import Repository


def update_pkgver(repositories: List[Repository], pkgver: str):
    for repository in repositories:
        repository.update_packages_pkgver(pkgver=pkgver)

    print("\n")


def remove_dependency(repositories: List[Repository], dependency: str):
    for repository in repositories:
        repository.remove_dependency(dependency=dependency)


def build(repositories):
    for repository in repositories:
        repository.sort()

        for package in repository.packages:
            package.build()
