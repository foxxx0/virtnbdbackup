"""
    Copyright (C) 2021  Michael Ablassmeier <abi@grinser.de>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import sys
import zipfile
import logging

from datetime import datetime
from libvirtnbdbackup.outputhelper import exceptions

log = logging.getLogger(__name__)


class outputHelper:
    """Directs output stream to either regular directory or
    zipfile. If other formats are added class should be
    used as generic wrapper for open()/write()/close() functions.
    """

    class Directory:
        """Backup to target directory"""

        def __init__(self, targetDir):
            self.targetDir = targetDir
            self.fileHandle = None
            if self.targetDir is not None:
                self._makeDir()

        def _makeDir(self):
            """Create output directoy on init"""
            if os.path.exists(self.targetDir):
                if not os.path.isdir(self.targetDir):
                    raise exceptions.OutputCreateDirectory(
                        "Specified target is a file, not a directory"
                    )
            if not os.path.exists(self.targetDir):
                try:
                    os.makedirs(self.targetDir)
                except OSError as e:
                    raise exceptions.OutputCreateDirectory(
                        "Cant create target directory:", e
                    )

        def open(self, targetFile, mode="wb"):
            """Open target file"""
            try:
                # pylint: disable=unspecified-encoding,consider-using-with
                self.fileHandle = open(targetFile, mode)
                return self.fileHandle
            except OSError as e:
                raise exceptions.OutputOpenException(
                    f"Unable to open target file: [{targetFile}]: {e}"
                ) from e

        def write(self, data):
            """Write wrapper"""
            return self.fileHandle.write(data)

        def flush(self):
            """Flush wrapper"""
            return self.fileHandle.flush()

        def close(self):
            """Close wrapper"""
            return self.fileHandle.close()

    class Zip:
        """Backup to zip file"""

        def __init__(self):
            self.zipStream = None
            self.zipFileStream = None

            log.info("Writing zip file stream to stdout")
            try:
                # pylint: disable=consider-using-with
                self.zipStream = zipfile.ZipFile(
                    sys.stdout.buffer, "x", zipfile.ZIP_STORED
                )
            except zipfile.error as e:
                raise exceptions.OutputOpenException(
                    f"Unable to open zip stream: {e}"
                ) from e

        def open(self, fileName, mode="w"):
            """Open wrapper"""
            zipFile = zipfile.ZipInfo(
                filename=fileName,
            )
            now = datetime.now()
            zipFile.date_time = now.replace(microsecond=0).timetuple()
            zipFile.compress_type = zipfile.ZIP_STORED

            try:
                # pylint: disable=consider-using-with
                self.zipFileStream = self.zipStream.open(
                    zipFile, mode, force_zip64=True
                )
                return self.zipFileStream
            except zipfile.error as e:
                raise exceptions.OutputOpenException(
                    f"Unable to open zip stream: {e}"
                ) from e

            return False

        def close(self):
            """Close wrapper"""
            return self.zipFileStream.close()

        def write(self, data):
            """Write wrapper"""
            return self.zipFileStream.write(data)
