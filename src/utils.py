import ctypes
import json
import locale
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
import webbrowser
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from contextlib import contextmanager
from ctypes import wintypes
from tkinter import filedialog

import easygui
import keyboard
import mouse
import yaml
from watchdog.events import FileSystemEventHandler

VERSION = '1.3'
APP_NAME = 'LOLauncher'
REPO_NAME = 'danielzimiao/TFTLauncher'
SUPPORTED_PRODUCTS = ['league_of_legends', 'teamfighttactics']
PRODUCT_DISPLAY_NAMES = {
    'league_of_legends': '英雄联盟',
    'teamfighttactics': '云顶之弈',
}
SUPPORTED_PATCH_LINES = ['live', 'pbe']
DEFAULT_PRODUCT = 'league_of_legends'
DEFAULT_PATCH_LINE = 'live'
DEFAULT_DRIVE = r"C:"
PROGRAM_DATA_DIR = os.environ.get('PROGRAMDATA', rf"{DEFAULT_DRIVE}\ProgramData")
METADATA_ROOT = os.path.join(PROGRAM_DATA_DIR, "Riot Games", "Metadata")
METADATA_DIR_FORMAT = os.path.join(METADATA_ROOT, "{product}.{patch_line}")
METADATA_FILE_FORMAT = "{product}.{patch_line}.product_settings.yaml"
DEFAULT_METADATA_DIR = METADATA_DIR_FORMAT.format(
    product=DEFAULT_PRODUCT, patch_line=DEFAULT_PATCH_LINE)
DEFAULT_METADATA_FILE = os.path.join(DEFAULT_METADATA_DIR, METADATA_FILE_FORMAT.format(
    product=DEFAULT_PRODUCT, patch_line=DEFAULT_PATCH_LINE))
UPDATE_CHECK_TIMEOUT_SECONDS = 3

LOCALE_CODES = {
    "zh_CN": "简体中文（国服）",
    "zh_MY": "简体中文（马来西亚）",
    "zh_TW": "繁体中文",
    "en_US": "英语（美国）",
    "en_GB": "英语（英国）",
    "en_AU": "英语（澳大利亚）",
    "en_PH": "英语（菲律宾）",
    "en_SG": "英语（新加坡）",
    "ja_JP": "日语",
    "ko_KR": "韩语",
    "cs_CZ": "捷克语",
    "de_DE": "德语",
    "el_GR": "希腊语",
    "es_AR": "西班牙语（阿根廷）",
    "es_ES": "西班牙语（西班牙）",
    "es_MX": "西班牙语（墨西哥）",
    "fr_FR": "法语（法国）",
    "hu_HU": "匈牙利语",
    "it_IT": "意大利语",
    "pl_PL": "波兰语",
    "pt_BR": "葡萄牙语（巴西）",
    "ro_RO": "罗马尼亚语",
    "ru_RU": "俄语",
    "th_TH": "泰语",
    "tr_TR": "土耳其语",
    "vi_VN": "越南语",
}

COMMENT_PREFIX = "#"

DEFAULT_QUICK_CHATS = [
    "Hello!",
    "/all press d to see your latency",
    "/all glhf",
    "/all gg",
    "/muteself",
    "/mute all",
    "/remake",
]

HOME_DIR = os.path.expanduser("~")
CONFIG_DIR = os.path.join(HOME_DIR, ".lolauncher")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILENAME = os.path.join(CONFIG_DIR, "config.json")
GUI_CONFIG_FILENAME = os.path.join(CONFIG_DIR, "gui_config.json")
QUICK_CHAT_FILENAME = os.path.join(CONFIG_DIR, "quick_chat.txt")
QUICK_CHAT_DOC = r"https://www.bilibili.com/read/cv35772066"

HOST = '127.0.0.1'
PORT = 65432


########################################################################################
class FileWatcher(FileSystemEventHandler):

    def __init__(self, *watching_files, selected_locale, msg_callback_fn=None):
        self.watching_files = filter_existing_files(watching_files)
        print(f"Watching files: {self.watching_files}")
        self.selected_locale = selected_locale
        self.msg_callback_fn = msg_callback_fn or print
        super().__init__()

    def on_modified(self, event):
        print(f'event type: {event.event_type}  path : {event.src_path}')
        if normalize_file_path(event.src_path) in self.watching_files:
            print(f'File {event.src_path} has been modified')
            content = read_yaml(event.src_path)
            if not is_valid_settings(content):
                print(f"Invalid file: {event.src_path}")
                return
            curr_locale = content['settings']['locale']
            if curr_locale != self.selected_locale:
                self.msg_callback_fn(f'正在将语言 {curr_locale} 更新为 {self.selected_locale} ...')
                update_settings(event.src_path, self.selected_locale, self.msg_callback_fn)


@contextmanager
def write_permission(file_path):
    try:
        os.chmod(file_path, stat.S_IWRITE)
        yield
    finally:
        os.chmod(file_path, stat.S_IREAD)
        pass


def is_running(process_name):
    try:
        commands = ['tasklist', '/FI', f'ImageName eq {process_name}', '/FI', 'Status eq Running', '/FO', 'LIST']
        default_encoding = locale.getpreferredencoding()
        output = subprocess.check_output(commands, creationflags=subprocess.CREATE_NO_WINDOW).decode(default_encoding)
        match = re.search(r'PID:\s+(\d+)', output)
        if match:
            pid = int(match.group(1))
            return pid
    except Exception as e:
        print(f"Error checking if {process_name} is running: {e}")


def is_foreground_window(pid):
    foreground_window = ctypes.windll.user32.GetForegroundWindow()
    pid_foreground_window = wintypes.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(foreground_window, ctypes.byref(pid_foreground_window))
    return pid_foreground_window.value == pid


def bring_to_foreground(pid):
    """
    Bring the window of the process to the front and simulate a mouse click
    :param pid: the process ID
    """

    def enum_windows_proc(hwnd, lparam):
        pid_window = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_window))
        if pid_window.value == pid:
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.SetFocus(hwnd)
            mouse.click()  # Assume pid is a full screen app
            return False  # stop enumerating windows
        return True  # continue enumerating windows

    enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(enum_windows_proc)
    ctypes.windll.user32.EnumWindows(enum_windows_proc, 0)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def open_repo_page():
    webbrowser.open(f"https://github.com/{REPO_NAME}")


def open_my_homepage():
    webbrowser.open("https://chenglongma.com")


def open_web(url):
    webbrowser.open(url)


def read_json(file_path):
    try:
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}


def version_key(version):
    numbers = [int(part) for part in re.findall(r'\d+', version or '')]
    return tuple((numbers + [0, 0, 0])[:3])


def get_updates(repo_name, current_version, timeout=UPDATE_CHECK_TIMEOUT_SECONDS):
    try:
        request = Request(
            f"https://api.github.com/repos/{repo_name}/releases/latest",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"{APP_NAME}/{current_version}",
            })
        with urlopen(request, timeout=timeout) as response:
            latest_release = json.load(response)
        latest_version = latest_release.get('tag_name', '')
        if version_key(latest_version) > version_key(current_version):
            return latest_version, latest_release.get('html_url')
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        pass

    return None, None


def prompt_for_update(new_version, html_url):
    print(f"发现新版本: {new_version}\n{html_url}")
    decision = easygui.buttonbox(
        f"发现新版本: {new_version}\n您要更新吗？",
        "发现新版本",
        ["前往下载", "继续使用该版本"])
    if decision == "前往下载":
        print("前往下载...")
        webbrowser.open(html_url)
    else:
        print("继续使用该版本")


def check_for_updates(no_new_version_callback=None):
    new_version, html_url = get_updates(REPO_NAME, VERSION)
    if new_version:
        prompt_for_update(new_version, html_url)
        return
    no_new_version_callback = no_new_version_callback or print
    no_new_version_callback()


def normalize_file_path(file_path):
    file_path = os.path.abspath(file_path)
    file_path = os.path.realpath(file_path)
    file_path = os.path.normpath(file_path)
    return file_path


def filter_existing_files(file_paths):
    return list(set(filter(os.path.exists, map(normalize_file_path, file_paths))))


def filter_valid_metadata_files(*file_paths):
    valid_files = []
    seen_files = set()
    for file_path in file_paths:
        if not file_path:
            continue
        normalized_file = normalize_file_path(file_path)
        if normalized_file not in seen_files and is_valid_metadata_file(normalized_file):
            seen_files.add(normalized_file)
            valid_files.append(normalized_file)
    return valid_files


def get_metadata_product(file_path):
    filename = os.path.basename(file_path).lower()
    for product in SUPPORTED_PRODUCTS:
        if filename.startswith(f"{product}."):
            return product
    return None


def to_list(data):
    if data is None or data == '':
        return []
    if isinstance(data, (list, tuple)):
        return list(data)
    return [data]


def backup_file(file_path):
    shutil.copyfile(file_path, file_path + '.bak')


def restore_file(file_path):
    backup_file_path = file_path + ".bak"
    if os.path.exists(backup_file_path):
        os.remove(file_path)
        os.rename(backup_file_path, file_path)
        print(f"Restore file: {file_path}")
    else:
        print(f"Backup file not found: {backup_file_path}")


def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def read_yaml(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return data
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def write_yaml(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def open_metadata_file_dialog(title, file_types, initial_dir=DEFAULT_METADATA_DIR,
                              initial_file=DEFAULT_METADATA_FILE, multiple=False):
    dialog = filedialog.askopenfilenames if multiple else filedialog.askopenfilename
    selected = dialog(title=title, filetypes=file_types, initialdir=initial_dir, initialfile=initial_file)
    selected_files = filter_valid_metadata_files(*to_list(selected))
    if multiple:
        return selected_files
    return selected_files[0] if selected_files else None


def find_setting_files():
    while True:
        selected_files = open_metadata_file_dialog(
            title="请选择英雄联盟和/或云顶之弈的 product_settings.yaml 文件",
            file_types=[('Riot 配置文件', '*.yaml'), ('所有文件', '*.*')],
            initial_dir=DEFAULT_METADATA_DIR,
            initial_file=DEFAULT_METADATA_FILE,
            multiple=True)
        if len(selected_files) > 0:
            return selected_files
        else:
            decision = easygui.buttonbox(
                "您要重新选择文件，还是退出？\n",
                "您选择了无效文件",
                ["重新选择", "退出"])
            if decision.lower() == '重新选择':
                continue
            elif decision.lower() == '退出':
                print("再见！")
                sys.exit()


def is_valid_settings(settings):
    return settings is not None and 'settings' in settings and 'locale_data' in settings


def is_valid_metadata_file(filename):
    if not os.path.exists(filename):
        return False
    settings = read_yaml(filename)
    return is_valid_settings(settings)


def detect_metadata_file(metadata_root=None):
    print("Detecting metadata file...")
    setting_files = []
    metadata_root = metadata_root or METADATA_ROOT

    for product in SUPPORTED_PRODUCTS:
        for patch_line in SUPPORTED_PATCH_LINES:
            product_id = f"{product}.{patch_line}"
            filename = os.path.join(
                metadata_root,
                product_id,
                f"{product_id}.product_settings.yaml")
            if is_valid_metadata_file(filename):
                print(f"Found metadata file: {filename}")
                setting_files.append(normalize_file_path(filename))
    return setting_files


def verify_metadata_file(config) -> [str]:
    setting_files = detect_metadata_file()
    setting_files = filter_valid_metadata_files(*to_list(config.get('SettingFile', [])), *setting_files)
    if not setting_files or len(setting_files) < 1:
        decision = easygui.buttonbox("配置文件通常位于：\n\n"
                                     "[系统盘]:\\ProgramData\\Riot Games\\Metadata\\"
                                     "[league_of_legends|teamfighttactics].[live|pbe]\\"
                                     "*.product_settings.yaml",
                                     "未找到配置文件，请手动选择", ["手动选择", "退出"])
        if decision.lower() == '手动选择':
            setting_files = find_setting_files()
        else:
            sys.exit()
    return setting_files


def is_read_only(file_path):
    file_stat = os.stat(file_path)
    return not bool(file_stat.st_mode & stat.S_IWRITE)


def update_settings(setting_file, selected_locale, msg_callback_fn=None):
    msg_callback_fn = msg_callback_fn or print
    try:
        setting_content = read_yaml(setting_file)
        if not is_valid_settings(setting_content):
            msg_callback_fn(f"无效文件: {setting_file}")
            return
        current_locale = setting_content['settings']['locale']
        if current_locale != selected_locale:
            msg_callback_fn(f"正在备份文件...")
            backup_file(setting_file)
        setting_content['settings']['locale'] = selected_locale
        if is_read_only(setting_file):
            msg_callback_fn(f"文件只读，无法更新: {setting_file}")
            return setting_content
        write_yaml(setting_file, setting_content)
        msg_callback_fn(f"更新设置文件成功!")
        return setting_content
    except Exception as e:
        msg_callback_fn(f"更新设置文件失败: {setting_file}, error: {e}")


def create_quick_chat_file(config_filename):
    file_path = config_filename if os.path.isdir(config_filename) else os.path.dirname(config_filename)

    file_path = os.path.join(file_path, 'quick_chat.txt')
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'{COMMENT_PREFIX} 设置快速聊天消息，一行一个\n')
            f.write(f'{COMMENT_PREFIX} 以 "{COMMENT_PREFIX}" 开头的行将被忽略\n')
            f.write(f'{COMMENT_PREFIX} 编辑完成后记得保存 :)\n\n')
            f.writelines("\n".join(DEFAULT_QUICK_CHATS))


def go_to_previous_window():
    # Get a handle to the foreground window
    foreground_window = ctypes.windll.user32.GetForegroundWindow()

    # Get a handle to the next window in the Z order
    next_window = ctypes.windll.user32.GetWindow(foreground_window, 2)

    # Bring the next window to the foreground
    ctypes.windll.user32.SetForegroundWindow(next_window)


def send_text(text):
    keyboard.send('enter')
    time.sleep(0.05)
    keyboard.write(text)
    keyboard.send('enter')


def show_existing_instance():
    try:
        with socket.create_connection((HOST, PORT), timeout=1) as conn:
            conn.sendall(b'SHOW_YOURSELF\n')
            print('Another instance is running, message sent.')
        return True
    except Exception:
        return False

def start_server(on_message_callback):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    def handle_client(conn, addr):
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8').strip()
                on_message_callback(message)

    def listen_loop():
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

    thread = threading.Thread(target=listen_loop, daemon=True)
    thread.start()

def singleton(mutex_name='LOLauncher'):
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    if ctypes.windll.kernel32.GetLastError() == 183:
        return False
    return True

