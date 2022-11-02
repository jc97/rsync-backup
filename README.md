# Hierarchical Configurable Differential Backup

This project is a simple Python tool for rsync backups.
Its main feature is performing one recursive rsync backup of a path with different configurations for certain sub paths.
The following example (see also [example.py](example.py)) illustrates this:

```python
backup.main(
    {
        "example": backup.Backup(
            source=Path("/home/myuser"),
            destination=Path("/media/myuser/usb-hdd/notebook_backup/current"),
            versions=Path("../versions"),
            config={
                backup.SOURCE_ROOT: backup.BackupFlag.KEEP_VERSIONS,
                Path(".cache/"): backup.BackupFlag.EXCLUDE,
                Path("Downloads/"): backup.BackupFlag.EXCLUDE,
                Path("Pictures/"): backup.BackupFlag.KEEP_DELETED_FILES,
                Path(".local/"): backup.BackupFlag.NONE,
            }
        )
    }
)
```

In this example we like to create a backup of our home directory.
Thereby, rsync should create a backup of updated files on the destination path (`--backup` option of rsync) in `../version/`.
The `KEEP_VERSIONS` flag indicates this option in this Python tool.
If a file was removed from our home directory, it should be removed from the destination drive too.
However, rsync should create a backup copy in `../versions/`. This corresponds to the rsync arguments `--backup --delete`.

However, we don't need a backup of `~/.cache/` and `~/Downloads/`. Thus, we can exclude them using it the `EXCLUDE` flag.

Moreover, files in `~/Pictures` should not be removed from the destination if they are removed from the source.
Thus, rsync should be executed without the `--delete` argument for `~/Pictures`.
This is indicated by the `KEEP_DELETED_FILES` flag.

Furthermore, `~/.local/` should be included in the backup, but we don't need old versions of its files.
Thus, rsync should create a "normal" backup resulting in an exact copy of the current state without saving old file versions (thus, using the `--delete` option, but not `--backup`).
This is indicated by using no actual flag (`NONE` flag).

As a result this tool would run the following rsync commands:

```
$ example.py run example

rsync -vPha --numeric-ids --stats --delete --delete-after -b --backup-dir /media/myuser/usb-hdd/notebook_backup/current/../versions/20221102_033632 --exclude /.cache/** --exclude /Downloads/** --exclude /Pictures/** --exclude /.local/** /home/myuser/ /media/myuser/usb-hdd/notebook_backup/current/

rsync -vPha --numeric-ids --stats /home/myuser/Pictures/ /media/myuser/usb-hdd/notebook_backup/current/Pictures/

rsync -vPha --numeric-ids --stats --delete --delete-after /home/myuser/.local/ /media/myuser/usb-hdd/notebook_backup/current/.local/
```

## Usage

This tool needs be wrapped by another Python script passing the backup configurations (e.g., [example.py](example.py))

```
$ python example.py 
usage: differential-backup [-h] {run,list,find} ...

positional arguments:
  {run,list,find}  action
    run            run a backup
    list           list defined backups
    find           find old versions of files

optional arguments:
  -h, --help       show this help message and exit
```

```
$ python example.py run -h
usage: differential-backup run [-h] [--simulate] BACKUP

positional arguments:
  BACKUP          The backup to execute.

optional arguments:
  -h, --help      show this help message and exit
  --simulate, -s  Dry run of rsync (-n argument)
```