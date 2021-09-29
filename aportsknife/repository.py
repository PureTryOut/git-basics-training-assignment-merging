import subprocess


class Repository():
    def __init__(self, path, packages):
        self.path = path
        self.name = path.name
        self.packages = packages

    def sort(self):
        packages_to_sort = []
        for package in self.packages:
            packages_to_sort.append(package.short_name)

        ret = subprocess.run([
            "ap",
            "builddirs",
            "-d",
            self.path] +
            packages_to_sort, check=True, capture_output=True)
        sorted_packages = ret.stdout.decode().split("\n")

        packages = []
        for sorted_package in sorted_packages:
            for package in self.packages:
                if package.path.replace("/APKBUILD", "") == sorted_package:
                    packages.append(package)

        self.packages = packages

    def update_packages_pkgver(self, pkgver_old, pkgver_new):
        for package in self.packages:
            package.update_pkgver(pkgver_old, pkgver_new)
            package.update_checksums()
