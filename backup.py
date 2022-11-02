import argparse
from dataclasses import dataclass
from datetime import datetime
from enum import auto, Flag
import os.path
from pathlib import Path
import shlex
from typing import Dict, List, Optional

RSYNC_BINARY = "rsync"
SOURCE_ROOT = Path(".")


class BackupFlag(Flag):
    NONE = auto()
    KEEP_VERSIONS = auto()
    KEEP_DELETED_FILES = auto()
    EXCLUDE = auto()


@dataclass
class Backup:
    source: Path
    destination: Path
    versions: Optional[Path]
    check_file: Optional[Path]

    config: Dict[Path, Optional[BackupFlag]]

    relative_exclude_list: Optional[List[str]] = None

    def list_file_versions(self, needle: Path) -> None:
        if self.versions is None:
            raise ValueError("No directory for old versions configured")
        if not self.versions.is_absolute():
            self.versions = self.destination / self.versions
        if not self.versions.exists():
            raise FileNotFoundError("Path " + str(self.versions) + " does not exist.")
        for backup_dir in sorted(self.versions.iterdir(), key=os.path.getctime, reverse=True):
            if backup_dir.is_dir():
                if (backup_dir / needle).exists():
                    file = backup_dir / needle
                    print("Version: File Date: {0} Backup: {1}".format(
                        datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        backup_dir.name
                    ))

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
            if not dry:
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
                # if element e is sub path of p, delete e
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
        if BackupFlag.KEEP_VERSIONS in config:
            if self.versions is None:
                raise ValueError("No directory for versions configured")
            args += ['-b', '--backup-dir', str(self.versions / sub_path)]
        for e in excluded.keys():
            args += ["--exclude", "/"+str(e.relative_to(sub_path))+"/**"]
        if self.relative_exclude_list:
            for e in self.relative_exclude_list:
                args += ["--exclude", e]
        args += [str(self.source / sub_path)+"/", str(self.destination / sub_path)+"/"]
        command_line = [RSYNC_BINARY] + args
        print(" ".join(command_line))
        os.system(shlex.join(command_line))
        for e in excluded.keys():
            if BackupFlag.EXCLUDE not in excluded[e]:
                print("")
                print("---")
                print("")
                self._backup_directory(e, dry)


def main(backups: Optional[Dict[str, Backup]] = None):
    if backups is None:
        backups = {}
    parser = argparse.ArgumentParser(prog="differential-backup",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    action_parser = parser.add_subparsers(help="action", dest='action')

    run_parser = action_parser.add_parser('run', help="run a backup")
    run_parser.add_argument('--simulate', '-s', action='store_true', help="Dry run of rsync (-n argument)")
    run_parser.add_argument(
        "backup",
        metavar="BACKUP",
        choices=backups.keys(),
        help="The backup to execute."
    )

    list_parser = action_parser.add_parser('list', help="list defined backups")

    find_parser = action_parser.add_parser('find', help="find old versions of files")
    find_parser.add_argument(
        "backup",
        metavar="BACKUP",
        choices=backups.keys(),
        help="The backup to use."
    )
    find_parser.add_argument(
        "path",
        metavar="PATH",
        type=Path,
        help="The path to look for."
    )

    args = parser.parse_args()
    if args.action == 'list':
        list_backups(backups)
    elif args.action == 'run':
        backups[args.backup].run(dry=args.simulate)
    elif args.action == "find":
        backups[args.backup].list_file_versions(args.path)
    else:
        parser.print_help()


def list_backups(backups: Dict[str, Backup]):
    for backup in backups.keys():
        print(backup)


if __name__ == "__main__":
    main()
