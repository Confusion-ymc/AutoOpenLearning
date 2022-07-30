import logging
import os
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import requests
import urllib3
from requests import Timeout
from tqdm import tqdm

try:
    import winreg  # 和注册表交互
except:
    pass

logger = logging.getLogger(__name__)


# chrome_version 文件设置浏览器配置


def get_chrome_version():
    try:
        # 从注册表中获得版本号
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')

        _v, data_type = winreg.QueryValueEx(key, 'version')

        print('Current Chrome Version: {}'.format(_v))  # 这步打印会在命令行窗口显示

        return _v  # 返回前3位版本号

    except Exception as e:
        print('check Chrome failed:{}  load from version file'.format(e))
        version_path = Path('chrome_version')
        if not version_path.is_file():
            return None
        with open(version_path, 'r') as f:
            data = f.read()
            return data or None


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
            zf.extractall(str(path))
    logger.warning(f'extracted to: {path}')


def webdriver_executable(chrome_version, download_folder=Path('drivers')) -> Path:
    exe_name = 'chromedriver'
    version_path = chrome_version.replace('.', '')
    webdriver_executable_map = {
        'mac': download_folder / version_path / exe_name,
        'win32': download_folder / version_path / (exe_name + '.exe'),
        'win64': download_folder / version_path / (exe_name + '.exe'),
    }
    """Get path of the chromium executable."""
    return webdriver_executable_map[current_platform()]


def find_version(version):
    url_map = {
        'win32': f'chromedriver_win32.zip',
        'win64': f'chromedriver_win32.zip',
        'mac': f'chromedriver_mac64.zip'
    }
    # base_url = 'http://npm.taobao.org'
    # url = base_url + '/mirrors/chromedriver/'
    base_url = 'https://registry.npmmirror.com/-/binary/chromedriver/'
    try:
        res = requests.get(base_url, timeout=30)
    except Timeout:
        raise Exception('获取webdriver版本超时')
    res_text = res.text
    res_json = res.json()
    if res.status_code != 200:
        raise Exception(f'url: {base_url}, res: {res_text}')
    # version_list = re.findall(r'<a href="(.*?)">(.*?)/</a> ', res_text)
    version_list = [i['name'] for i in res_json]
    version_list = version_list[::-1]
    version_len = len(version)
    for i in range(version_len):
        for item_version in version_list:
            if version[0:version_len - i] in item_version:
                match_version = item_version
                match_url = base_url + item_version + url_map[current_platform()]
                # print(match_url, match_version)
                return match_url, match_version
    raise Exception('not find available version')


def install_webdriver(chrome_version, download_folder=Path('drivers')) -> None:
    """Download chromdriver if not install."""
    version_path = chrome_version.replace('.', '')
    match_url, match_version = find_version(chrome_version)
    if not webdriver_executable(download_folder, chrome_version).exists():
        extract_zip(download_zip(match_url), download_folder / version_path)
    else:
        pass
        # logging.getLogger(__name__).warning('webdriver is already installed.')


def download_stealth_js():
    if not (Path.cwd() / 'stealth.min.js').exists():
        url = 'https://raw.githubusercontent.com/kingname/stealth.min.js/main/stealth.min.js'
        data = download_zip(url)
        with open('stealth.min.js', 'wb') as f:
            f.write(data.read())
    else:
        logging.getLogger(__name__).warning('stealth.min.js is already installed.')


def get_driver(chrome_version):
    download_folder = Path(os.getcwd() + '/drivers')
    install_webdriver(download_folder, chrome_version)
    return str(webdriver_executable(download_folder, chrome_version))
    # driver = webdriver.Chrome(service=Service(str(webdriver_executable(download_folder))))
    # driver.implicitly_wait(30)  # 隐性等待时间为30秒
    # return driver