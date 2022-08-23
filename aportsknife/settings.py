# SPDX-FileCopyrightText: 2022 Bart Ribbers <bribbers@disroot.org>
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

import xdg
import yaml


class Settings:
    def __init__(self):
        loaded_settings = yaml.safe_load(
            open(
                xdg.BaseDirectory.save_config_path("aportsknife") + "/config.yaml",
                "r",
            )
        )

        self.aports_path = Path(loaded_settings["aports_path"])
