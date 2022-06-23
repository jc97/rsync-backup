import os.path
from dataclasses import dataclass
from datetime import datetime
from enum import auto, Flag
from pathlib import Path
import shlex
from typing import Dict, Optional

RSYNC_BINARY = "rsync"


class BackupFlag(Flag):
    NONE = auto()
    KEEP_VERSION = auto()
    KEEP_DELETED_FILES = auto()
    EXCLUDE = auto()


@dataclass
class Backup:
    source: Path
    destination: Path
    versions: Optional[Path]
    check_file: Optional[Path]

    config: Dict[Path, Optional[BackupFlag]]

    def run(self, dry: bool = False) -> None:
        if self.check_file:
            if not self.check_file.is_absolute():
                self.check_file = self.destination / self.check_file
            if not self.check_file.exists():
                raise FileNotFoundError("Check file " + str(self.check_file) + " does not exist.")
        if self.versions is not None:
            if not self.versions.is_absolute():
                self.versions = self.destination / self.versions
            subdir = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.versions /= subdir
            self.versions.mkdir()
        self._backup_directory(Path("./"), dry)

    def _get_path_config(self, path: Path) -> BackupFlag:
        result_path: Optional[Path] = None
        result_flags = None
        for p in self.config.keys():
            if p == path:
                return self.config[p]
            if self._is_sub_path(p, path):
                if result_path is not None:
                    if self._is_sub_path(p, result_path):
                        continue
                result_path = p
                result_flags = self.config[p]
        return result_flags

    @staticmethod
    def _is_sub_path(parent: Path, child: Path) -> bool:
        if child == parent:
            return False
        return parent in child.parents

    def _backup_directory(self, sub_path: Path, dry: bool = False) -> None:
        config = self._get_path_config(sub_path)
        if BackupFlag.EXCLUDE in config:
            return
        excluded: Dict[Path, BackupFlag] = {}
        for p in self.config.keys():
            if not self._is_sub_path(sub_path, p):
                continue
            include = True
            for e in excluded.keys():
                if self._is_sub_path(e, p):
                    include = False
                    break
                # wenn element subpath von p: element löschen und p einfügen
                if self._is_sub_path(p, e):
                    excluded.pop(e)
            if include:
                excluded[p] = self.config[p]
        args = [
            '-vPha',
            '--numeric-ids',
            '--stats'
        ]
        if dry:
            args += ["-n"]
        if BackupFlag.KEEP_DELETED_FILES not in config:
            args += ['--delete', '--delete-after']
        if BackupFlag.KEEP_VERSION in config:
            if self.versions is None:
                raise ValueError("No directory for versions configured")
            args += ['-b', '--backup-dir', str(self.versions)]
        for e in excluded.keys():
            args += ["--exclude", str(e)+"/**"]
        args += [str(self.source / sub_path)+"/", str(self.destination / sub_path)+"/"]
        command_line = [RSYNC_BINARY] + args
        print(" ".join(command_line))
        os.system(shlex.join(command_line))
        for e in excluded.keys():
            if BackupFlag.EXCLUDE not in excluded[e]:
                self._backup_directory(e, dry)


def main():
    pass


if __name__ == "__main__":
    main()
