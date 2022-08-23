# SPDX-FileCopyrightText: 2022 Bart Ribbers <bribbers@disroot.org>
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
        return self.path == other.path

    def __str__(self) -> str:
        return self.long_name

    def update_pkgver(self, pkgver):
        apkbuild = self.path / "APKBUILD"
        tmp_apkbuild = self.path / "APKBUILD~"

        os.rename(apkbuild, tmp_apkbuild)
        destination = open(apkbuild, "w")
        source = open(tmp_apkbuild, "r")

        for line in source:
            if "pkgver=" in line:
                line = line.replace(line.split("=")[1], pkgver + "\n")
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
            subprocess.run(["abuild", "checksum"], check=True, capture_output=True)
            print(".", end="", flush=True)
        except subprocess.CalledProcessError:
            print("\nSomething went wrong while updating checksums of " + f"{self.path}")
            print('Please run "abuild checksum" in the package to ' + "determine the issue")

            exit(1)

    def build(self):
        os.chdir(self.path)

        try:
            print(f"Building {self.long_name}", end="... ", flush=True)
            subprocess.run(["abuild", "rootbld"], check=True, capture_output=True)
            print("Done!")
        except subprocess.CalledProcessError as ex:
            print(f"\nSomething went wrong while building {self.long_name}")
            filename = BaseDirectory.save_data_path("aportsknife/build/") + self.name
            with open(filename, "w") as log_file:
                log_file.write(ex.output.decode())
                print(f"The build log is written to {filename}")

            exit(0)
