# SPDX-FileCopyrightText: 2020 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import subprocess

from xdg import BaseDirectory


class Package():
    def __init__(self, repository_root, path):
        self.repository_root = repository_root
        self.path = path
        self.repository = path.rsplit('/', 3)[1]
        self.short_name = path.rsplit('/', 2)[1]
        self.long_name = f"{self.repository}/{self.short_name}"

    def __eq__(self, other):
        if self.path == other.path:
            return True
        return False

    def update_pkgver(self, pkgver_old, pkgver_new):
        os.rename(self.path, self.path + '~')
        destination = open(self.path, 'w')
        source = open(self.path + '~', 'r')

        for line in source:
            if "pkgver=" in line and pkgver_old in line:
                line = line.replace(pkgver_old, pkgver_new)
            elif "pkgrel=" in line:
                line = line.replace(line, "pkgrel=0\n")

            destination.write(line)

        # Make sure we clean up after ourselves
        destination.close()
        source.close()
        os.remove(self.path + '~')

    def update_checksums(self):
        os.chdir(os.path.dirname(self.path))

        failure = False
        try:
            subprocess.check_output(["abuild", "checksum"])
            print(".", end="", flush=True)
        except subprocess.CalledProcessError as ex:
            failure = True
            print(f"Something went wrong while updating checksums of " +
                  f"{self.path}")
            print("Please run \"abuild checksum\" in the package to " +
                  "determine the issue")
        finally:
            os.chdir(self.repository_root)

            if failure:
                exit(1)

    def build(self):
        os.chdir(os.path.dirname(self.path))

        print(f"Building {self.long_name}", end="... ", flush=True)
        result = subprocess.run(["abuild", "rootbld"], capture_output=True,
                                text=True)

        if result.returncode == 0:
            print("Done!")
        else:
            print(f"\nSomething went wrong while building {self.long_name}")
            filename = BaseDirectory.save_data_path(
                f"aportsknife/build/{self.repository}/") + self.short_name
            with open(filename, 'w') as log_file:
                log_file.write(result.stdout)
                log_file.write(result.stderr)
                print(f"The build log is written to {filename}")

            skip_package = input("Do you want to skip this package while " +
                                 "building next time? ")
            if skip_package in ["true", "yes", "y"]:
                filename = (BaseDirectory.save_data_path("aportsknife") +
                            "/skip_packages.txt")
                if not os.path.isfile(filename):
                    open(filename, 'x')

                with open(filename, 'a') as skip_file:
                    skip_file.write(self.long_name + "\n")

                print(f"\n{self.long_name} will be skipped in subsequence " +
                      "runs")
                print(f"If you don't want to skip it anymore, remove it " +
                      "from " + BaseDirectory.save_data_path("aportsknife") +
                      "/skip_packages.txt")

        os.chdir(self.repository_root)
