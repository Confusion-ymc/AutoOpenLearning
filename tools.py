import logging
import re
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import requests
import urllib3
from tqdm import tqdm

logger = logging.getLogger(__name__)
DOWNLOADS_FOLDER = Path.cwd() / 'drivers'


def download_zip(url: str) -> BytesIO:
    """Download data from url."""
    logger.warning('Starting download. ' 'Download may take a few minutes.')
    with urllib3.PoolManager() as http:
        # Get data from url.
        # set preload_content=False means using stream later.
        r = http.request('GET', url, preload_content=False)
        if r.status >= 400:
            raise OSError(f'downloadable not found at {url}: ' f'Received {r.data.decode()}.\n')

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
    zip_path = path / 'temp.zip'
    if current_platform() == 'mac':
        import subprocess
        import shutil
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
        else:
            if zip_path.exists():
                zip_path.unlink()
    else:
        with ZipFile(data) as zf:
            zf.extractall(str(zip_path))
    logger.warning(f'extracted to: {zip_path}')


def webdriver_executable(version) -> Path:
    exe_name = 'chromedriver'
    version_path = version.replace('.', '')
    webdriver_executable_map = {
        'mac': DOWNLOADS_FOLDER / version_path / exe_name,
        'win32': DOWNLOADS_FOLDER / version_path / (exe_name + '.exe'),
        'win64': DOWNLOADS_FOLDER / version_path / (exe_name + '.exe'),
    }
    """Get path of the chromium executable."""
    return webdriver_executable_map[current_platform()]


def find_version(version='95.0.4638.54'):
    url_map = {
        'win32': f'chromedriver_win32.zip',
        'win64': f'chromedriver_win32.zip',
        'mac': f'chromedriver_mac64.zip'
    }
    base_url = 'http://npm.taobao.org'
    res = requests.get(base_url + '/mirrors/chromedriver/').text
    version_list = re.findall(r'<a href="(.*?)">(.*?)/</a> ', res)
    version_list = version_list[::-1]
    version_len = len(version)
    for i in range(version_len):
        for item_url, item_version in version_list:
            if version[0:version_len - i] in item_version:
                match_version = item_version
                match_url = base_url + item_url + url_map[current_platform()]
                print(match_url, match_version)
                return match_url, match_version


def install_webdriver(version) -> None:
    """Download chromdriver if not install."""
    version_path = version.replace('.', '')
    match_url, match_version = find_version(version)
    if not webdriver_executable(version_path).exists():
        extract_zip(download_zip(match_url), DOWNLOADS_FOLDER / version_path)

    else:
        logging.getLogger(__name__).warning('webdriver is already installed.')


def download_stealth_js():
    if not (Path.cwd() / 'stealth.min.js').exists():
        url = 'https://raw.githubusercontent.com/kingname/stealth.min.js/main/stealth.min.js'
        data = download_zip(url)
        with open('stealth.min.js', 'wb') as f:
            f.write(data.read())
    else:
        logging.getLogger(__name__).warning('stealth.min.js is already installed.')
