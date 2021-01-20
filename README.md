# aportsknife

This script is a "swiss knife" tool for Alpine Linux aports.
Features:
- Mass-update pkgver of groups of packages (e.g. KDE Plasma from 5.20.4 to 5.20.5)
- Mass build all packages in the repository

## Dependencies

Required dependencies:
- `abuild`

Optional dependencies for building:
- `git`
- `lua-aports`
- `alpine-sdk`
- `abuild-rootbld`

## Installation

```
$ pip install .
```

## License

![GPL-3.0-or-later logo](https://www.gnu.org/graphics/gplv3-127x51.png)

This program is licensed under GNU General Public License, version 3 or later
