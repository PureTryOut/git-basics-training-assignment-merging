# SPDX-FileCopyrightText: 2022 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

import tomlkit
import xdg


class Settings:
    def __init__(self):
        with open(
            xdg.BaseDirectory.save_config_path("aportsknife") + "/config.toml",
            "r",
            encoding="utf-8",
        ) as setting_file:
            loaded_settings = tomlkit.parse(setting_file.read())

            self.aports_path = Path(loaded_settings["general"]["aports_path"])
