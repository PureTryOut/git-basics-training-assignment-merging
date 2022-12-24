# SPDX-FileCopyrightText: 2022 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess


class Repository:
    def __init__(self, path, packages):
        self.path = path
        self.name = path.name
        self.packages = packages

    def __eq__(self, other) -> bool:
        return self.name == other.name

    def sort(self):
        packages_to_sort = []
        for package in self.packages:
            packages_to_sort.append(package.name)

        ret = subprocess.run(
            ["ap", "builddirs", "-d", self.path] + packages_to_sort,
            check=True,
            capture_output=True,
        )
        sorted_packages = ret.stdout.decode().split("\n")

        packages = []
        for sorted_package in sorted_packages:
            for package in self.packages:
                if str(package.path) == sorted_package:
                    packages.append(package)

        self.packages = packages

    def update_packages_pkgver(self, pkgver):
        for package in self.packages:
            package.update_pkgver(pkgver)
