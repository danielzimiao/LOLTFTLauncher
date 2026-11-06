<p align="center">
    <img src="./docs/icon.svg" alt="LOLauncher logo" width="400px">
</p>

<div align="center">

![macOS Version](https://img.shields.io/badge/WinOS_Version-10%2B-green?logo=windows)
[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/danielzimiao/TFTLauncher?include_prereleases)](https://github.com/danielzimiao/TFTLauncher/releases/latest)
[![GitHub License](https://img.shields.io/github/license/danielzimiao/TFTLauncher)](https://github.com/danielzimiao/TFTLauncher/blob/main/LICENSE)
[![Bilibili](https://img.shields.io/badge/使用教程-Bilibili-1E88E5?logo=bilibili)](https://www.bilibili.com/video/BV1vk3keeEfd/?share_source=copy_web&vd_source=cc52ec064b8a1a36acc686a244981a42)
[![Bilibili](https://img.shields.io/badge/手动设置教程-Bilibili-1E88E5?logo=bilibili)](https://www.bilibili.com/video/BV1Zs421P7EB)
[![Downloads](https://img.shields.io/github/downloads/danielzimiao/TFTLauncher/total)](https://github.com/danielzimiao/TFTLauncher/releases/latest)

</div>

# 英雄联盟 & 云顶之弈，启动！

* 该程序用于修改英雄联盟和独立版云顶之弈（Teamfight Tactics）的语言，例如选择 **简体中文（国服）**。
* 程序会自动检测 LOL 与 TFT 的 `live` / `pbe` 配置文件；默认点击一次启动按钮会将两者统一修改为所选语言并持续监控，防止 Riot 更新配置后恢复默认值。
* 自 [v1.1.0](https://github.com/ChenglongMa/LOLauncher/releases/tag/1.1.0) 版本后，该程序新增 **一键喊话**。
* 该程序目前面向 Windows 10/11；独立 TFT 客户端适配从 v1.3.0 开始提供。

## v1.3.0：独立 TFT 客户端适配

Riot 将 TFT 拆分为独立客户端后，它使用单独的产品配置：

- 英雄联盟：`league_of_legends.live` / `league_of_legends.pbe`
- 云顶之弈：`teamfighttactics.live` / `teamfighttactics.pbe`

本版本会同时查找这些产品的 `product_settings.yaml`。只要账户已按 Riot 的默认流程安装 LOL 和 TFT，无需额外指定 TFT 安装目录；选择语言并点击启动按钮后，程序会同时更新已安装的 LOL 与 TFT。TFT 未安装时，程序仍可照常只处理 LOL。

如需只修改其中一个游戏，可在带有右箭头的二级菜单“设置 → 语言适用范围 ▶”中选择“仅英雄联盟”或“仅云顶之弈”。默认值为“英雄联盟 & 云顶之弈”，选择会保存在 `config.json` 中。

> [!WARNING]
> 仅修改一个游戏时，程序会显示风险提示。英雄联盟与云顶之弈会共享 Riot Client 的部分启动和跳转流程；从英雄联盟客户端跳转到云顶之弈或在两个游戏之间切换时，语言设置不同步可能导致语言不一致、翻译不完整，或被 Riot 恢复为默认语言。没有特殊需求时建议保留默认范围。

> [!IMPORTANT]
> 首次测试建议先完全退出 Riot Client、LOL 与 TFT，再运行本程序。点击启动后请保持程序在后台，等待 Riot Client 完成所需语言资源更新，然后进入游戏检查文本。`一键喊话`仍是英雄联盟专用功能。

### v1.3.1：启动性能优化

- 配置探测直接读取 Windows 的 `%ProgramData%\Riot Games\Metadata`，不再遍历所有逻辑盘和离线映射盘。
- 主界面会先显示，再在后台查找客户端；查找期间显示进度条并暂时禁用启动按钮，避免用户因无反馈而反复双击。
- 自动更新检查改为窗口显示后在后台执行，不再阻塞主界面启动。
- 移除 PyGithub 及其间接依赖，缩小单文件打包体积并减少解压加载时间。

> [!NOTE]
> 虽然该软件看上去 **久不更新**，但这是因为该机制还有效。如果失效，我会马上修复的。
> 
> 总之：
> 
> _该程序永久**免费**且**持续更新**，如果您喜欢该项目，欢迎点一个⭐！_
> 

_如果您有任何问题或新的功能需求，请在 [Discussions](https://github.com/ChenglongMa/LOLauncher/discussions) 或 [Issues](https://github.com/ChenglongMa/LOLauncher/issues) 中讨论，也可以给我发邮件 [chenglong.m_at_outlook.com](mailto:chenglong.m@outlook.com)。_

_谢谢关注！_

## 视频教程

[![tutorial](./docs/tutorial.png)](https://www.bilibili.com/video/BV1vk3keeEfd/?share_source=copy_web&vd_source=cc52ec064b8a1a36acc686a244981a42)

## 安装并运行

1. 前往 [Release 页面](https://github.com/danielzimiao/TFTLauncher/releases/latest) 下载最新版 ZIP，并解压到任意目录。
2. 完全退出正在运行的 Riot Client、英雄联盟和云顶之弈，然后运行 `LOLauncher.exe`。
3. 选择目标语言。程序默认同时处理英雄联盟 & 云顶之弈；如有特殊需求，可通过“设置 → 语言适用范围 ▶”只选择其中一个。
4. 点击启动按钮并保持程序在后台，等待 Riot Client 完成所需语言资源更新后再进入游戏。

### 程序界面

![LOLauncher](./docs/LOLauncher.png)

## 版本比较

| 功能 | [v1.0.1](https://github.com/ChenglongMa/LOLauncher/releases/tag/1.0.1) | [v1.0.2](https://github.com/ChenglongMa/LOLauncher/releases/tag/1.0.2) | [v1.1.0](https://github.com/ChenglongMa/LOLauncher/releases/tag/1.1.0) | [v1.2.0](https://github.com/ChenglongMa/LOLauncher/releases/tag/1.2.0) | v1.3.0 | v1.3.1 |
|---|---:|---:|---:|---:|---:|---:|
| Windows 10 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Windows 11 | X | ✔ | ✔ | ✔ | ✔ | ✔ |
| **非**管理员权限 | X | ✔ | ✔ | ✔ | ✔ | ✔ |
| 后台运行 | X | ✔ | ✔ | ✔ | ✔ | ✔ |
| 自动更新 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| 一键喊话 | X | X | ✔ | ✔ | ✔ | ✔ |
| 暗黑模式 | X | X | X | ✔ | ✔ | ✔ |
| 独立云顶之弈客户端支持 | X | X | X | X | ✔ | ✔ |
| 英雄联盟 & 云顶之弈适用范围选择 | X | X | X | X | ✔ | ✔ |
| 快速启动优化 | X | X | X | X | X | ✔ |


### 注意 
1. ~~该程序需要**管理员权限**运行。这是因为需要将游戏的配置文件设置为只读，以防止游戏更新后恢复默认语言。~~
   * 自 1.0.2 版本开始，不再需要管理员权限。
2. ~~游戏启动成功后**不需要**再次运行该程序，可按照您的习惯启动游戏。若之后游戏更新导致语言恢复，可重新运行该程序。~~
   * 自 1.0.2 版本开始，程序需要保持后台运行，直到游戏启动，以便在游戏更新后自动修改语言。
   * 您依然可以按照您的习惯启动游戏，但是**启动游戏前**请不要关闭该程序。
3. 本程序会**自动检查更新**，如果有新版本会提示您下载。我会根据游戏的更新情况及时更新程序。

> [!TIP]
> 
> 如果您想要完整的翻译, 请在打开游戏后先**关闭一次**, 然后会弹出以下界面:
> 
> <img alt="更新按钮" src="docs/update-prompt.png" width="80%"/>
> 
> 请**毫不犹豫**地点击 `更新` 按钮!
> 
> 之后进入游戏就会看到完整的翻译了 🍻
> 
> (比较遗憾的是, 该操作目前无法通过程序自动完成, 且下次启动会失效, 但是我会尽快想办法更新程序以支持该功能)

*如果你想手动配置相关文件路径，可以参考以下文档：*

## 功能介绍

### 1. 修改游戏语言

如 [程序界面](#程序界面) 所示，启动游戏前，您可以选择游戏语言。程序会把同一语言应用到自动检测到的 LOL 与 TFT 配置。

> [!NOTE]
> 
> 只有**简体中文（国服）** 是带有语音的，其他语言只有文本。
> 
> TFT 的可用文本与语音资源由 Riot 当前版本决定；本程序负责设置客户端语言，不修改游戏资源文件。
>

### 2. 一键喊话

您可以设置英雄联盟一键喊话的**快捷键**以及**喊话内容**。独立 TFT 客户端不使用该功能。

> [!IMPORTANT]
> 
> 1. 请将游戏窗口模式设置为**无边框全屏**。
> 2. 使用`一键喊话`前请确保聊天框处于**关闭**状态。
> 3. 开启`一键喊话`后建议先开一局自定义或训练模式测试一下。
> 
> 详细信息请参考 [一键喊话功能的注意事项](https://www.bilibili.com/read/cv35772066)。
> 

## 配置文件

首次运行程序后，会在`C:\Users\<你的用户名>\.lolauncher`下生成 `config.json` 文件，你可以在该文件中手动配置相关路径。

```json
{
  "SettingFile": [
    "C:\\ProgramData\\Riot Games\\Metadata\\league_of_legends.live\\league_of_legends.live.product_settings.yaml",
    "C:\\ProgramData\\Riot Games\\Metadata\\teamfighttactics.live\\teamfighttactics.live.product_settings.yaml"
  ],
  "GameClient": "D:/Riot Games/Riot Client/RiotClientServices.exe",
  "Locale": "zh_CN",
  "ProductScope": "all"
}
```

- `SettingFile`：Riot 产品配置文件路径列表，可同时包含英雄联盟与云顶之弈的 `live` / `pbe` YAML。程序通常会自动检测，无需手工填写。
- `GameClient`：Riot 客户端<img src="./docs/lol_client.ico" alt="Riot 客户端 icon" width="40px">的 `RiotClientServices.exe` 文件路径。
- `Locale`：游戏语言，例如 `zh_CN` 为中文，`en_US` 为英文。
- `ProductScope`：语言适用范围。`all` 表示同时修改两者，也可设为 `league_of_legends` 或 `teamfighttactics`。
- **注意：路径中的 `\` 需要替换为 `\\`，或者使用 `/` （请参考以上示例）。**
- 其他配置尽量从程序界面中修改，避免手动修改。

## 声明

本项目是一个用于设置英雄联盟与云顶之弈客户端语言的工具，其目的是提供更好的游戏体验。它只修改 Riot 的产品设置 YAML，不修改游戏核心文件、不影响游戏机制，也不提供任何形式的不公平优势。

与此相反，游戏作弊器通常会修改游戏的核心文件，或者以某种方式影响游戏的机制，以提供不公平的优势。这种行为不仅违反了游戏的服务条款，也破坏了游戏的公平性和玩家的游戏体验。

因此，LOLauncher与游戏作弊器在本质上是完全不同的。请放心使用。🖖

## 常见问题

### 1. 程序失效，游戏语言未修改成功。

**解决方案**：您可以参考视频教程 [![youtube](https://img.shields.io/badge/YouTube_版本-FF0000?logo=youtube)](https://youtu.be/gNkLY6EAsaU?si=Q-WdWD7Jt7Oyik_w) 或 [![Bilibili](https://img.shields.io/badge/Bilibili_版本-white?logo=bilibili)](https://www.bilibili.com/video/BV1Zs421P7EB) 手动修改游戏语言。

如果依然有问题，请在 [Discussions](https://github.com/ChenglongMa/LOLauncher/discussions) 或 [Issues](https://github.com/ChenglongMa/LOLauncher/issues) 中讨论，也可以给我发邮件 [chenglong.m_at_outlook.com](mailto:chenglong.m@outlook.com)。

如果只有 TFT 没有生效，请在“设置”中执行“自动检测游戏配置文件”，并确认 `%ProgramData%\Riot Games\Metadata\teamfighttactics.live\teamfighttactics.live.product_settings.yaml` 已出现在 `config.json` 的 `SettingFile` 列表中。

### 2. 运行程序时弹出 `Windows Defender 防病毒` 警告。

**解决方案**：这是由于该程序没有签名导致的。该程序代码完全开源，只是数字证书太贵了，我无力购买🥺。

如果您信任该程序，请点击 `More info`（`更多信息`），然后点击 `Run anyway`（`仍要运行`）。

该操作只需一次，后续不会再弹出警告。

<img alt="Windows Defender" src="./docs/win-warning1.png" width="80%"/>
<img alt="Windows Run" src="./docs/win-warning2.png" width="80%"/>
