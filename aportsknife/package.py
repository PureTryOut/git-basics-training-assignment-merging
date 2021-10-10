# SPDX-FileCopyrightText: 2020 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import subprocess

from xdg import BaseDirectory


class Package:
    def __init__(self, repository, name):
        self.repository = repository
        self.path = repository.path / f"{name}"
        self.name = name
        self.long_name = f"{repository.name}/{name}"

    def __eq__(self, other) -> bool:
        if self.path == other.path:
            return True
        return False

    def __str__(self) -> str:
        return self.long_name

    def update_pkgver(self, pkgver_old, pkgver_new):
        apkbuild = self.path / "APKBUILD"
        tmp_apkbuild = self.path / "APKBUILD~"

        os.rename(apkbuild, tmp_apkbuild)
        destination = open(apkbuild, "w")
        source = open(tmp_apkbuild, "r")

        for line in source:
            if "pkgver=" in line and pkgver_old in line:
                line = line.replace(pkgver_old, pkgver_new)
            elif "pkgrel=" in line:
                line = line.replace(line, "pkgrel=0\n")

            destination.write(line)

        # Make sure we clean up after ourselves
        destination.close()
        source.close()
        os.remove(tmp_apkbuild)

        self.update_checksums()

    def update_checksums(self):
        os.chdir(self.path)

        try:
            subprocess.run(
                ["abuild", "checksum"], check=True, capture_output=True
            )
            print(".", end="", flush=True)
        except subprocess.CalledProcessError:
            print(
                "Something went wrong while updating checksums of "
                + f"{self.path}"
            )
            print(
                'Please run "abuild checksum" in the package to '
                + "determine the issue"
            )

            exit(1)

    def build(self):
        os.chdir(self.path)

        try:
            print(f"Building {self.long_name}", end="... ", flush=True)
            subprocess.run(
                ["abuild", "rootbld"], check=True, capture_output=True
            )
            print("Done!")
        except subprocess.CalledProcessError as ex:
            print(f"\nSomething went wrong while building {self.long_name}")
            filename = (
                BaseDirectory.save_data_path("aportsknife/build/") + self.name
            )
            with open(filename, "w") as log_file:
                log_file.write(ex.output.decode())
                print(f"The build log is written to {filename}")

            skip_package = input(
                "Do you want to skip this package while "
                + "building next time? "
            )
            if skip_package in ["true", "yes", "y"]:
                filename = (
                    BaseDirectory.save_data_path("aportsknife")
                    + "/skip_packages.txt"
                )
                if not os.path.isfile(filename):
                    open(filename, "x")

                with open(filename, "a") as skip_file:
                    skip_file.write(self.long_name + "\n")

                print(
                    f"\n{self.long_name} will be skipped in subsequence "
                    + "runs"
                )
                print(
                    "If you don't want to skip it anymore, remove it "
                    + "from "
                    + BaseDirectory.save_data_path("aportsknife")
                    + "/skip_packages.txt"
                )
