from pathlib import Path

import backup

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
