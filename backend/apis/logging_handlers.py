import os
import io
import shutil
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler


class DatedSubdirTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    TimedRotatingFileHandler that moves rotated files into a date-based subfolder.

    Example:
      base filename: /path/logs/django.log
      on rotation at midnight -> /path/logs/2025-08-09/django.log

    Notes:
    - Current day's logs are written to the base file (django.log).
    - When rotation happens, the file is moved into a YYYY-MM-DD subfolder.
    - backupCount applies to number of rotated files kept (by date) per handler.
    """

    def __init__(self, filename, when='midnight', interval=1, backupCount=14, encoding='utf-8', delay=True, utc=True, atTime=None):
        super().__init__(
            filename=filename,
            when=when,
            interval=interval,
            backupCount=backupCount,
            encoding=encoding,
            delay=delay,
            utc=utc,
            atTime=atTime,
        )

        # Customize destination path via namer/rotator
        def namer(default_name: str) -> str:
            # default_name looks like: /logs/django.log.YYYY-MM-DD
            # Extract date suffix
            # Find the last occurrence of '.log.' pattern
            marker = '.log.'
            idx = default_name.rfind(marker)
            if idx != -1:
                base_dir = os.path.dirname(os.path.dirname(default_name))  # up to /logs
                date_suffix = default_name[idx + len(marker):]  # YYYY-MM-DD
                # Ensure we only take the date component if extra parts exist
                date_suffix = date_suffix.split("_")[0]
                dated_dir = os.path.join(base_dir, os.path.basename(os.path.dirname(default_name)), date_suffix)
                return os.path.join(dated_dir, os.path.basename(self.baseFilename))

            # Fallback: put into today's folder
            date_suffix = datetime.utcnow().strftime('%Y-%m-%d')
            base_dir = os.path.dirname(self.baseFilename)
            dated_dir = os.path.join(base_dir, date_suffix)
            return os.path.join(dated_dir, os.path.basename(self.baseFilename))

        def rotator(source: str, dest: str) -> None:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            # Move/rename file
            try:
                os.replace(source, dest)
            except OSError:
                # If cross-device, fall back to copy+remove
                with open(source, 'rb') as sf, open(dest, 'wb') as df:
                    shutil.copyfileobj(sf, df)
                try:
                    os.remove(source)
                except OSError:
                    pass

        self.namer = namer
        self.rotator = rotator

    def purge_old(self):
        """Delete dated subfolders older than backupCount days."""
        try:
            base_dir = os.path.dirname(self.baseFilename)
            keep_days = max(int(self.backupCount or 0), 0)
            if keep_days <= 0:
                return
            cutoff = datetime.utcnow() - timedelta(days=keep_days)
            for entry in os.scandir(base_dir):
                if not entry.is_dir():
                    continue
                # Expect YYYY-MM-DD
                try:
                    dt = datetime.strptime(entry.name, '%Y-%m-%d')
                except ValueError:
                    continue
                if dt < cutoff:
                    try:
                        shutil.rmtree(entry.path)
                    except OSError:
                        pass
        except Exception:
            pass

    def doRollover(self):
        super().doRollover()
        # After rolling over, purge old dated folders
        self.purge_old()


