import threading
import tkinter as tk
from queue import Empty, Queue
from tkinter import ttk, messagebox, font
import sv_ttk

import pystray
from PIL import Image, ImageDraw, ImageFont, ImageTk
from watchdog.observers import Observer

from assets import get_asset
from ui.quick_chat import QuickChatDialog
from ui.utils import create_warning_label, THEME_COLOR
from utils import *


def change_font(font_family):
    for font_name in font.names():
        _font = font.nametofont(font_name)
        _font.config(family=font_family)


class App:
    def __init__(self, setting_files, config, gui_config):
        self.setting_files: [str] = setting_files
        self.config = config
        self.ui_config = gui_config
        self.locale_dict = {value: key for key, value in LOCALE_CODES.items()}
        self.game_client = config.get("GameClient", "")
        self.observers: [Observer] = []
        self.update_check_queue = Queue()
        self.metadata_detection_queue = Queue()
        self.metadata_detection_running = False
        self.metadata_loading = True

        self.root = tk.Tk()
        self.theme: str = self.ui_config.get("Theme", "light")
        if "dark" in self.theme.lower():
            sv_ttk.use_dark_theme()
        else:
            sv_ttk.use_light_theme()
        change_font("Microsoft YaHei UI")
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.window_width = 350
        self.window_height = 450
        self.control_padding = 10
        self.layout_padding = 15

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.position_top = int(self.screen_height / 2 - self.window_height / 2)
        self.position_right = int(self.screen_width / 2 - self.window_width / 2)
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.position_right}+{self.position_top}")
        self.root.iconbitmap(get_asset('icon.ico'))
        self.root.minsize(self.window_width, self.window_height)
        self.root.maxsize(self.window_width + 50, self.window_height + 50)
        # self.root.resizable(False, False)

        saved_product_scope = self.config.get("ProductScope", "all")
        valid_product_scopes = ["all", *SUPPORTED_PRODUCTS]
        if saved_product_scope not in valid_product_scopes:
            saved_product_scope = "all"
        self.product_scope_var = tk.StringVar(value=saved_product_scope)

        self.create_menu_bar()
        self.selected_locale = config.get("Locale", "zh_CN")
        if self.selected_locale not in LOCALE_CODES.keys():
            self.selected_locale = "zh_CN"
        self.create_locale_groupbox()
        self.create_quick_chat_groupbox()

        self.create_status_bar()
        self.create_metadata_progress()
        self.create_launch_button()
        self.tray_app = self.create_tray_app()
        self.tray_thread = threading.Thread(target=self.tray_app.run)

        self.root.pack_propagate(True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_window_minimizing)

    def create_tray_app(self):
        return pystray.Icon(
            APP_NAME,
            Image.open(get_asset("tray_icon.png")),
            f"{APP_NAME} v{VERSION}",
            menu=self.create_tray_menu()
        )

    def create_tray_menu(self):
        return pystray.Menu(
            pystray.MenuItem("显示主窗口", self.on_window_restoring, default=True),
            pystray.MenuItem("一键喊话", self.set_quick_chat, checked=lambda item: self.quick_chat_enabled_setting),
            pystray.MenuItem("帮助", self.show_about),
            pystray.MenuItem("退出", self.on_window_closing)
        )

    def set_quick_chat(self, icon, item):
        print("Quick chat enabled:", item.checked)
        current_state = self.quick_chat_enabled.get()
        self.quick_chat_enabled.set(not current_state)
        self.quick_chat_enabled_setting = not current_state

    def set_process_name(self):
        process_name = easygui.enterbox("请输入进程名称", "设置进程名称", self.config.get("Process Name", "League of Legends.exe"))
        if process_name:
            self.config["Process Name"] = process_name
            self.sync_config()
            self.update_status(f"进程名称已设置为：{process_name}")

    def create_menu_bar(self):
        self.menu_bar = tk.Menu(self.root)
        self.setting_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.setting_menu.add_command(label="自动检测游戏配置文件", command=self.detect_metadata_file)
        self.setting_menu.add_command(label="手动选择游戏配置文件", command=self.choose_metadata_file)
        self.product_scope_menu = tk.Menu(self.setting_menu, tearoff=0)
        self.product_scope_menu.add_radiobutton(
            label="英雄联盟 & 云顶之弈（默认）",
            variable=self.product_scope_var,
            value="all",
            command=self.on_product_scope_changed)
        self.product_scope_menu.add_radiobutton(
            label="仅英雄联盟（可能影响跨客户端跳转）",
            variable=self.product_scope_var,
            value="league_of_legends",
            command=self.on_product_scope_changed)
        self.product_scope_menu.add_radiobutton(
            label="仅云顶之弈（可能影响跨客户端跳转）",
            variable=self.product_scope_var,
            value="teamfighttactics",
            command=self.on_product_scope_changed)
        self.setting_menu.add_cascade(label="语言适用范围  ▶", menu=self.product_scope_menu)
        self.setting_menu.add_command(label="设置进程名称", command=self.set_process_name)
        self.setting_menu.add_separator()
        self.setting_menu.add_command(label="切换颜色主题", command=lambda: self.root.after(0, self.toggle_theme))
        self.minimize_on_closing = tk.BooleanVar(value=self.config.get("MinimizeOnClosing", True))
        self.setting_menu.add_checkbutton(label="关闭时最小化到托盘", variable=self.minimize_on_closing)
        self.menu_bar.add_cascade(label="设置", menu=self.setting_menu)
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="关于", command=self.show_about)
        self.help_menu.add_command(label="检查更新", command=lambda: check_for_updates(self.no_new_version_fn))
        self.menu_bar.add_cascade(label="帮助", menu=self.help_menu)
        self.root.config(menu=self.menu_bar)

    def toggle_theme(self):
        sv_ttk.toggle_theme()
        self.theme = sv_ttk.get_theme()
        self.quick_chat_warning_label.config(background=THEME_COLOR[self.theme]["warning_bg"], foreground=THEME_COLOR[self.theme]["warning_fg"])
        self.quick_chat_warning_label.tag_config("link", foreground=THEME_COLOR[self.theme]["accent"], underline=True)
        self.create_custom_button_style()
        self.refresh_launch_button_image()

    def create_locale_groupbox(self):
        self.locale_groupbox = ttk.LabelFrame(self.root, text="语言设置", style='Card.TFrame')
        self.locale_var = tk.StringVar(value=LOCALE_CODES[self.selected_locale])
        self.locale_dropdown = ttk.Combobox(self.locale_groupbox, textvariable=self.locale_var, state="readonly", exportselection=True)
        self.locale_dropdown['values'] = list(self.locale_dict.keys())
        self.locale_dropdown.current(list(self.locale_dict.values()).index(self.selected_locale))
        self.locale_dropdown.pack(padx=self.control_padding, pady=self.control_padding, fill=tk.BOTH)
        self.locale_dropdown.bind("<<ComboboxSelected>>", self.on_locale_changed)
        self.locale_groupbox.pack(fill=tk.BOTH, padx=self.layout_padding, pady=self.layout_padding)

    def on_quick_chat_enable_change(self, *args):
        if not self.config.get("QuickChatNoteNotAsk", False) and self.quick_chat_enabled.get():
            decision = easygui.buttonbox('您是否已根据《注意事项》设置好"无边框"模式？',
                                         "启用前的准备", ["已设置好", "还没有", "已设置好，不要再提醒"])
            if not decision or decision == "还没有":
                self.quick_chat_enabled.set(False)
                self.quick_chat_enabled_setting = False
                self.tray_app.update_menu()
                return
            elif decision == "已设置好，不要再提醒":
                self.config["QuickChatNoteNotAsk"] = True

        state = tk.NORMAL if self.quick_chat_enabled.get() else tk.DISABLED
        self.shortcut_dropdown.config(state=state)
        self.set_chat_button.config(state=state)
        self.quick_chat_enabled_setting = self.quick_chat_enabled.get()
        self.tray_app.update_menu()
        if self.quick_chat_enabled_setting:
            self.update_status("一键喊话已启用")
            create_quick_chat_file(CONFIG_FILENAME)
            self.quick_chat_dialog.set_hotkey(self.shortcut_var.get())
        else:
            self.update_status("一键喊话已禁用")
            self.quick_chat_dialog.disable_hotkey()

    def create_quick_chat_groupbox(self):
        self.quick_chat_groupbox = ttk.LabelFrame(self.root, text="一键喊话设置", style='Card.TFrame')
        self.quick_chat_doc = self.config.get("QuickChatDoc", QUICK_CHAT_DOC)
        self.quick_chat_warning_label = create_warning_label(
            self.quick_chat_groupbox,
            "\u26A1 使用前请仔细阅读", "注意事项",
            self.quick_chat_doc,
            theme=self.theme
        )
        self.quick_chat_warning_label.pack(padx=self.control_padding, pady=self.control_padding, fill=tk.BOTH)
        self.quick_chat_enabled_setting = self.config.get("QuickChatEnabled", False)
        self.quick_chat_enabled = tk.BooleanVar(value=self.quick_chat_enabled_setting)
        self.quick_chat_enabled.trace("w", self.on_quick_chat_enable_change)

        self.quick_chat_checkbox = ttk.Checkbutton(self.quick_chat_groupbox, text="一键喊话", variable=self.quick_chat_enabled,
                                                   style='Switch.TCheckbutton')
        self.quick_chat_checkbox.pack()

        self.shortcut_frame = ttk.Frame(self.quick_chat_groupbox)

        self.shortcut_label = ttk.Label(self.shortcut_frame, text="快捷键")
        self.shortcut_label.pack(side=tk.LEFT, padx=self.control_padding)
        available_shortcuts = ["`", "Alt", "Ctrl", "Shift", "Tab"]
        setting_value = self.config.get("QuickChatShortcut", "`")
        if setting_value not in available_shortcuts:
            available_shortcuts.append(setting_value)
        self.shortcut_var = tk.StringVar(value=setting_value)

        state = "readonly" if self.quick_chat_enabled.get() else tk.DISABLED
        self.shortcut_dropdown = ttk.Combobox(self.shortcut_frame, state=state, textvariable=self.shortcut_var, exportselection=True)

        self.shortcut_dropdown['values'] = available_shortcuts
        self.shortcut_dropdown.current(available_shortcuts.index(self.shortcut_var.get()))
        self.shortcut_dropdown.bind("<<ComboboxSelected>>", self.on_shortcut_changed)
        self.shortcut_dropdown.pack(side=tk.RIGHT)

        self.shortcut_frame.pack(padx=self.layout_padding)

        state = tk.NORMAL if self.quick_chat_enabled.get() else tk.DISABLED
        self.set_chat_button = ttk.Button(self.quick_chat_groupbox, text="设置喊话内容", state=state, command=self.open_quick_chat_file)
        self.set_chat_button.pack(padx=self.control_padding, pady=self.control_padding, fill=tk.BOTH)

        self.quick_chat_groupbox.pack(fill=tk.BOTH, padx=self.layout_padding, pady=self.layout_padding)

        self.quick_chat_dialog = QuickChatDialog(self, self.config, self.ui_config)
        if self.quick_chat_enabled_setting:
            self.quick_chat_dialog.set_hotkey(self.config.get('QuickChatShortcut', '`'))
        else:
            self.quick_chat_dialog.disable_hotkey()

    def open_quick_chat_file(self):
        print("Opening quick chat file...")
        if not os.path.exists(QUICK_CHAT_FILENAME):
            create_quick_chat_file(CONFIG_FILENAME)
        subprocess.run(['notepad.exe', QUICK_CHAT_FILENAME], check=False)

    def create_custom_button_style(self):
        style = ttk.Style()
        style.configure('CustomAccent.TButton', padding=(8, 3))

    @staticmethod
    def load_launch_button_font(size, bold=False):
        windows_dir = os.environ.get("WINDIR", r"C:\Windows")
        font_name = "msyhbd.ttc" if bold else "msyh.ttc"
        font_path = os.path.join(windows_dir, "Fonts", font_name)
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            return ImageFont.load_default()

    def create_launch_button_image(self):
        width, height = 238, 50
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        is_dark = "dark" in self.theme.lower()
        foreground = "#f3f3f3" if is_dark else "#1f1f1f"
        divider = "#777777" if is_dark else "#9a9a9a"

        with Image.open(get_asset("button_icon.png")) as source_icon:
            icon = source_icon.convert("RGBA")
            icon.thumbnail((44, 46), Image.Resampling.LANCZOS)
        image.alpha_composite(icon, (0, (height - icon.height) // 2))

        game_font = self.load_launch_button_font(12, bold=True)
        launch_font = self.load_launch_button_font(17, bold=True)
        draw.text((96, 14), "英雄联盟", font=game_font, fill=foreground, anchor="mm")
        draw.text((96, 36), "云顶之弈", font=game_font, fill=foreground, anchor="mm")
        draw.line((150, 8, 150, height - 8), fill=divider, width=1)
        draw.text((196, height // 2), "启动！", font=launch_font, fill=foreground, anchor="mm")
        return ImageTk.PhotoImage(image, master=self.root)

    def refresh_launch_button_image(self):
        if not hasattr(self, "launch_button"):
            return
        self.launch_button_image = self.create_launch_button_image()
        self.launch_button.configure(image=self.launch_button_image)

    def create_launch_button(self):
        self.create_custom_button_style()
        self.launch_button_image = self.create_launch_button_image()
        self.launch_button = ttk.Button(
            self.root,
            image=self.launch_button_image,
            command=self.start,
            style="CustomAccent.TButton",
            state=tk.DISABLED if self.metadata_loading else tk.NORMAL,
            cursor="hand2",
            takefocus=True)
        self.launch_button.pack(
            side=tk.BOTTOM,
            pady=self.layout_padding)

    def create_status_bar(self):
        self.status_var = tk.StringVar(value="准备就绪")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.RIDGE, anchor=tk.W, foreground="gray")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_metadata_progress(self):
        self.metadata_progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.metadata_progress.pack(
            side=tk.BOTTOM,
            fill=tk.X,
            padx=self.layout_padding,
            pady=(0, self.control_padding))
        self.metadata_progress.start(12)
        self.update_status("正在查找英雄联盟 & 云顶之弈客户端...")

    def update_status(self, message):
        self.status_var.set(message)

    def show_about(self, icon=None, item=None):
        pady = self.layout_padding // 2
        self.about_window = tk.Toplevel(self.root)
        self.about_window.title("关于")
        self.about_window.iconbitmap(get_asset("icon.ico"))
        self.about_window.geometry(f"+{self.position_right}+{self.position_top}")
        self.about_window.protocol("WM_DELETE_WINDOW", lambda: self.on_about_window_closing(create_tray=icon is not None))
        self.app_name_label = tk.Label(self.about_window, text=f"{APP_NAME} v{VERSION}")
        self.app_name_label.pack(padx=self.control_padding, pady=pady)
        accent_color = THEME_COLOR[self.theme]["accent"]

        self.author_label = tk.Label(self.about_window, text="原作者：Chenglong Ma", fg=accent_color, cursor="hand2")
        self.author_label.pack(padx=self.control_padding, pady=pady)
        self.author_label.bind("<Button-1>", lambda event: open_my_homepage())

        self.tft_author_label = tk.Label(
            self.about_window,
            text="TFT 适配作者：danielzimiao",
            fg=accent_color,
            cursor="hand2")
        self.tft_author_label.pack(padx=self.control_padding, pady=pady)
        self.tft_author_label.bind(
            "<Button-1>",
            lambda event: open_web("https://github.com/danielzimiao"))

        self.homepage_label = tk.Label(self.about_window, text=f"GitHub：{REPO_NAME}", fg=accent_color, cursor="hand2")
        self.homepage_label.pack(padx=self.control_padding, pady=pady)
        self.homepage_label.bind("<Button-1>", lambda event: open_repo_page())

        self.copyright_label = tk.Label(self.about_window, text="Copyright © 2024 Chenglong Ma. All rights reserved.")
        self.copyright_label.pack(padx=self.control_padding, pady=pady)

    def on_about_window_closing(self, create_tray=False):
        self.about_window.destroy()

    def no_new_version_fn(self):
        messagebox.showinfo("检查更新", "当前已是最新版本")
        self.update_status("当前已是最新版本")

    def start_background_update_check(self):
        def fetch_update():
            self.update_check_queue.put(get_updates(REPO_NAME, VERSION))

        threading.Thread(target=fetch_update, daemon=True).start()
        self.root.after(100, self.poll_background_update_check)

    def poll_background_update_check(self):
        try:
            new_version, html_url = self.update_check_queue.get_nowait()
        except Empty:
            self.root.after(100, self.poll_background_update_check)
            return
        if new_version:
            prompt_for_update(new_version, html_url)

    def start_game(self, *settings):
        self.update_status("正在启动游戏...")
        game_clients_in_settings = [os.path.join(setting['product_install_root'], "Riot Client/RiotClientServices.exe") for setting in settings]
        game_clients = filter_existing_files(to_list(self.game_client) + game_clients_in_settings)
        if not game_clients or len(game_clients) == 0:
            self.update_status("未找到 RiotClientServices.exe，请手动启动游戏。")
            return
        if len(game_clients) > 1:
            msg = "请从以下选项中选择一个游戏启动路径"
            title = "找到多个游戏路径，请选择一个"
            choice = easygui.choicebox(msg, title, game_clients)
            if not choice:
                return
            game_clients = [choice]

        self.update_status("语言设置完成，正在启动 Riot 客户端！")
        self.game_client = os.path.normpath(game_clients[0])
        subprocess.run(['explorer.exe', self.game_client], check=False)

    def start(self):
        if self.metadata_loading:
            self.update_status("正在查找客户端，请稍候...")
            return
        self.update_status("正在更新配置文件...")
        settings = []
        active_setting_files = self.get_active_setting_files()
        if len(active_setting_files) == 0:
            selected_names = "、".join(PRODUCT_DISPLAY_NAMES[product] for product in self.get_selected_products())
            messagebox.showerror("错误", f"未找到{selected_names}的有效配置文件，请先自动检测或手动选择。")
            return

        for setting_file in active_setting_files:
            setting = update_settings(setting_file, self.selected_locale, msg_callback_fn=self.update_status)
            if setting:
                settings.append(setting)

        if len(settings) == 0:
            messagebox.showerror("错误", "配置文件更新失败，无法启动游戏。")
            return

        self.start_observers(active_setting_files)
        self.start_game(*settings)
        self.on_window_minimizing(True)

    def stop_observers(self):
        print("Stopping observer...")
        for observer in self.observers:
            if observer is not None and observer.is_alive():
                observer.stop()
                observer.join()
                print("Observer stopped")
        self.observers = []

    def start_observers(self, setting_files=None):
        setting_files = setting_files or self.get_active_setting_files()
        event_handler = FileWatcher(*setting_files, selected_locale=self.selected_locale)
        unique_dirs = set(os.path.dirname(file) for file in setting_files)
        for directory in unique_dirs:
            observer = Observer()
            observer.schedule(event_handler, path=directory, recursive=False)
            observer.start()
            self.observers.append(observer)
        print(f"Start Watching...")

    def get_selected_products(self):
        product_scope = self.product_scope_var.get()
        if product_scope == "all":
            return list(SUPPORTED_PRODUCTS)
        return [product_scope]

    def get_active_setting_files(self):
        selected_products = set(self.get_selected_products())
        return [setting_file for setting_file in self.setting_files
                if get_metadata_product(setting_file) in selected_products]

    def on_product_scope_changed(self):
        self.stop_observers()
        selected_products = self.get_selected_products()
        selected_names = " & ".join(PRODUCT_DISPLAY_NAMES[product] for product in selected_products)
        self.update_status(f"语言适用范围：{selected_names}")
        self.sync_config()
        if self.product_scope_var.get() != "all":
            messagebox.showwarning(
                "仅修改一个游戏可能导致问题",
                f"当前已选择仅修改{selected_names}。\n\n"
                "英雄联盟与云顶之弈会共享 Riot Client 的部分启动和跳转流程。"
                "如果从英雄联盟客户端跳转到云顶之弈，或在两个游戏之间切换，"
                "未同步修改的客户端可能出现语言不一致、翻译不完整，或被 Riot 恢复为默认语言。\n\n"
                "如果没有特殊需求，建议选择“英雄联盟 & 云顶之弈（默认）”。")

    def start_background_metadata_detection(self):
        if self.metadata_detection_running:
            return
        self.metadata_detection_running = True
        self.metadata_loading = True
        self.metadata_progress.pack(
            side=tk.BOTTOM,
            fill=tk.X,
            padx=self.layout_padding,
            pady=(0, self.control_padding),
            before=self.launch_button)
        self.metadata_progress.start(12)
        self.launch_button.configure(state=tk.DISABLED, cursor="")
        self.update_status("正在查找英雄联盟 & 云顶之弈客户端...")

        def detect_metadata():
            try:
                detected_files = detect_metadata_file()
                setting_files = filter_valid_metadata_files(
                    *to_list(self.config.get('SettingFile', [])),
                    *detected_files)
                self.metadata_detection_queue.put((setting_files, None))
            except Exception as error:
                self.metadata_detection_queue.put(([], error))

        threading.Thread(target=detect_metadata, daemon=True).start()
        self.root.after(100, self.poll_background_metadata_detection)

    def poll_background_metadata_detection(self):
        try:
            setting_files, error = self.metadata_detection_queue.get_nowait()
        except Empty:
            self.root.after(100, self.poll_background_metadata_detection)
            return

        self.metadata_detection_running = False
        self.metadata_loading = False
        self.metadata_progress.stop()
        self.metadata_progress.pack_forget()
        self.launch_button.configure(state=tk.NORMAL, cursor="hand2")

        if error:
            self.update_status("查找客户端配置时出现错误")
            messagebox.showerror("查找失败", f"查找客户端配置时出现错误：\n{error}")
            return

        if setting_files:
            self.setting_files = setting_files
            self.sync_config()
            products = {
                get_metadata_product(setting_file)
                for setting_file in setting_files
                if get_metadata_product(setting_file)
            }
            product_names = " & ".join(
                PRODUCT_DISPLAY_NAMES[product]
                for product in SUPPORTED_PRODUCTS
                if product in products)
            self.update_status(f"已找到{product_names}配置，共 {len(setting_files)} 个")
            return

        self.update_status("未找到英雄联盟或云顶之弈配置")
        choose_manually = messagebox.askyesno(
            "未找到客户端配置",
            "未找到英雄联盟或云顶之弈的 Riot 配置文件。\n是否手动选择 product_settings.yaml？")
        if choose_manually:
            self.choose_metadata_file(confirm=False)

    def detect_metadata_file(self):
        is_yes = tk.messagebox.askyesno("提示", "您确定要重新检测以修改已有配置？")
        if is_yes:
            self.start_background_metadata_detection()

    def choose_metadata_file(self, confirm=True):
        is_yes = not confirm or tk.messagebox.askyesno("提示", "已自动检测到游戏配置文件，您确定要手动选择吗？")
        if is_yes:
            selected_files = open_metadata_file_dialog(
                title="请选择英雄联盟和/或云顶之弈的 product_settings.yaml 文件",
                file_types=[('Riot 配置文件', '*.yaml'), ('所有文件', '*.*')],
                initial_dir=DEFAULT_METADATA_DIR,
                initial_file=DEFAULT_METADATA_FILE,
                multiple=True)
            if selected_files:
                self.setting_files = selected_files
                self.sync_config()
                msg = "游戏配置文件已更新"
            else:
                msg = "未找到有效配置，将继续使用之前的配置"
            self.update_status(msg)
            tk.messagebox.showinfo("提示", msg)

    def on_locale_changed(self, event):
        self.stop_observers()
        current_value = self.locale_var.get()
        self.selected_locale = self.locale_dict[current_value]
        self.update_status(f"语言将被设置为：{current_value}")

    def on_shortcut_changed(self, event):
        current_value = self.shortcut_var.get()
        self.update_status(f"快捷键将被设置为：{current_value}")
        self.quick_chat_dialog.set_hotkey(current_value)

    def on_window_restoring(self, icon: pystray.Icon = None, item=None):
        self.root.after(0, self.root.deiconify)

    def on_window_showing(self, event=None):
        if self.root.winfo_viewable():
            print("Window is already visible")
            return
        print("Window is now visible", event)

    def on_window_minimizing(self, force_minimize=False):
        print("Window is now minimized")
        if force_minimize or self.minimize_on_closing.get():
            self.sync_config()
            self.root.after(0, self.root.withdraw)
        else:
            self.on_window_closing(self.tray_app)

    def run(self):
        self.root.after(50, self.start_background_metadata_detection)
        self.root.after(250, self.start_background_update_check)
        self.tray_thread.start()
        self.root.mainloop()
        self.tray_thread.join()

    def sync_config(self):
        default_config = {
            "@注意": r"请使用\或/做为路径分隔符，如 C:\ProgramData 或 C:/ProgramData",
            "@SettingFile": "英雄联盟和云顶之弈 product_settings.yaml 文件路径列表",
            "SettingFile": self.setting_files,
            "@GameClient": "请在下方填写 RiotClientServices.exe 文件路径",
            "GameClient": self.game_client,
            "Locale": self.selected_locale,
            "ProductScope": self.product_scope_var.get(),
            "MinimizeOnClosing": self.minimize_on_closing.get(),
            "Process Name": self.config.get("Process Name", "League of Legends.exe"),
            "QuickChatEnabled": self.quick_chat_enabled.get(),
            "QuickChatShortcut": self.shortcut_var.get(),
            "QuickChatDoc": QUICK_CHAT_DOC,
        }
        self.config.update(default_config)
        self.config.update(self.quick_chat_dialog.user_config)
        write_json(CONFIG_FILENAME, self.config)
        self.ui_config["Theme"] = self.theme
        self.ui_config.update(self.quick_chat_dialog.ui_config)
        write_json(GUI_CONFIG_FILENAME, self.ui_config)
        print("Configuration file updated")

    def on_window_closing(self, icon: pystray.Icon = None, item=None):

        close = messagebox.askyesno("退出", "退出后再启动英雄联盟或云顶之弈时，语言可能恢复为默认设置\n您确定要退出吗？")
        if close:
            self.stop_observers()
            if icon:
                icon.stop()
            self.sync_config()
            self.root.after(0, self.root.destroy)


    def show_window(self):
        print('Showing window')

        if not self.root.winfo_viewable():
            self.root.deiconify()

        self.root.lift()
        self.root.focus_force()

        self.root.attributes('-topmost', True)
        self.root.attributes('-topmost', False)
