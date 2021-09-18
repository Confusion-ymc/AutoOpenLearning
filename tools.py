import logging
import stat
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import urllib3
from tqdm import tqdm

logger = logging.getLogger(__name__)
DOWNLOADS_FOLDER = Path.cwd() / 'drivers'
REVISION = '588429'
BASE_URL = 'https://storage.googleapis.com/chromium-browser-snapshots'
windowsArchive = 'chrome-win' if int(REVISION) > 591479 else 'chrome-win32'


def download_zip(url: str) -> BytesIO:
    """Download data from url."""
    logger.warning('Starting download. ' 'Download may take a few minutes.')

    # Uncomment the statement below to disable HTTPS warnings and allow
    # download without certificate verification. This is *strongly* as it
    # opens the code to man-in-the-middle (and other) vulnerabilities; see
    # https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
    # for more.
    # urllib3.disable_warnings()

    with urllib3.PoolManager() as http:
        # Get data from url.
        # set preload_content=False means using stream later.
        r = http.request('GET', url, preload_content=False)
        if r.status >= 400:
            raise OSError(f'Chromium downloadable not found at {url}: ' f'Received {r.data.decode()}.\n')

        # 10 * 1024
        _data = BytesIO()
        try:
            total_length = int(r.headers['content-length'])
        except (KeyError, ValueError, AttributeError):
            total_length = 0
        process_bar = tqdm(total=total_length, unit_scale=True, unit='b')
        for chunk in r.stream(10240):
            _data.write(chunk)
            process_bar.update(len(chunk))
        process_bar.close()

    logger.warning('download done.')
    return _data


def current_platform() -> str:
    """Get current platform name by short string."""
    if sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform.startswith('darwin'):
        return 'mac'
    elif sys.platform.startswith('win') or sys.platform.startswith('msys') or sys.platform.startswith('cyg'):
        if sys.maxsize > 2 ** 31 - 1:
            return 'win64'
        return 'win32'
    raise OSError('Unsupported platform: ' + sys.platform)


def extract_zip(data: BytesIO, path: Path) -> None:
    """Extract zipped data to path."""
    # On mac zipfile module cannot extract correctly, so use unzip instead.
    if current_platform() == 'mac':
        import subprocess
        import shutil

        zip_path = path / 'chrome.zip'
        if not path.exists():
            path.mkdir(parents=True)
        with zip_path.open('wb') as f:
            f.write(data.getvalue())
        if not shutil.which('unzip'):
            raise OSError('Failed to automatically extract chromium.' f'Please unzip {zip_path} manually.')
        proc = subprocess.run(
            ['unzip', str(zip_path)], cwd=str(path), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            logger.error(proc.stdout.decode())
            raise OSError(f'Failed to unzip {zip_path}.')
        if chromium_executable().exists() and zip_path.exists():
            zip_path.unlink()
    else:
        with ZipFile(data) as zf:
            zf.extractall(str(path))
    exec_path = chromium_executable()
    if not exec_path.exists():
        raise IOError('Failed to extract chromium.')
    exec_path.chmod(exec_path.stat().st_mode | stat.S_IXOTH | stat.S_IXGRP | stat.S_IXUSR)
    logger.warning(f'chromium extracted to: {path}')


def get_chromium_url():
    url_map = {
        'linux': f'{BASE_URL}/Linux_x64/{REVISION}/chrome-linux.zip',
        'mac': f'{BASE_URL}/Mac/{REVISION}/chrome-mac.zip',
        'win32': f'{BASE_URL}/Win/{REVISION}/{windowsArchive}.zip',
        'win64': f'{BASE_URL}/Win_x64/{REVISION}/{windowsArchive}.zip',
    }
    return url_map[current_platform()]


def get_webdriver_url():
    url_map = {
        'linux': 'https://chromedriver.storage.googleapis.com/2.46/chromedriver_linux64.zip',
        'win32': 'https://chromedriver.storage.googleapis.com/2.46/chromedriver_win32.zip',
        'win64': 'https://chromedriver.storage.googleapis.com/2.46/chromedriver_win32.zip',
        'mac': 'https://chromedriver.storage.googleapis.com/2.46/chromedriver_mac64.zip'
    }
    return url_map[current_platform()]


def chromium_executable() -> Path:
    chromium_executable_map = {
        'linux': DOWNLOADS_FOLDER / REVISION / 'chrome-linux' / 'chrome',
        'mac': (DOWNLOADS_FOLDER / REVISION / 'chrome-mac' / 'Chromium.app' / 'Contents' / 'MacOS' / 'Chromium'),
        'win32': DOWNLOADS_FOLDER / REVISION / windowsArchive / 'chrome.exe',
        'win64': DOWNLOADS_FOLDER / REVISION / windowsArchive / 'chrome.exe',
    }
    """Get path of the chromium executable."""
    return chromium_executable_map[current_platform()]


def webdriver_executable() -> Path:
    webdriver_executable_map = {
        'linux': DOWNLOADS_FOLDER / REVISION / 'chrome-linux' / 'chromedriver',
        'mac': DOWNLOADS_FOLDER / REVISION / 'chromedriver',
        'win32': DOWNLOADS_FOLDER / REVISION / 'chromedriver.exe',
        'win64': DOWNLOADS_FOLDER / REVISION / 'chromedriver.exe',
    }
    """Get path of the chromium executable."""
    return webdriver_executable_map[current_platform()]


def install_browser() -> None:
    """Download chromium if not install."""
    if not chromium_executable().exists():
        extract_zip(download_zip(get_chromium_url()), DOWNLOADS_FOLDER / REVISION)

    else:
        logging.getLogger(__name__).warning('chromium is already installed.')


def install_webdriver() -> None:
    """Download chromdriver if not install."""
    if not webdriver_executable().exists():
        extract_zip(download_zip(get_webdriver_url()), DOWNLOADS_FOLDER / REVISION)

    else:
        logging.getLogger(__name__).warning('webdriver is already installed.')
