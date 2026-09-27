# Niri + Clavis 桌面配置

这是从我的 Arch Linux 桌面整理出的 Niri + [Clavis Shell](https://github.com/StatIndet/quickshell) 配置与安装脚本。包含 Niri 键位、Clavis 的个性化设置、中文 Fuzzel、壁纸兜底，以及 Clavis 原生 QML 插件的库路径修复。

仓库不包含 Clavis 源码、账号密钥、个人壁纸或桌宠程序。Clavis 和 key-cli 由上游发布包安装；本仓库的模板在安装时生成当前用户的绝对路径。

## 使用条件

- Arch Linux x86_64，正常工作的网络、`sudo` 和 Niri 图形会话
- 以普通桌面用户运行，**不要使用 `sudo bash install.sh`**
- 已有配置会备份，但安装将替换当前用户的 Niri 与 Clavis 配置；先阅读 `config/` 中的键位和偏好
- 上游 `install-arch.sh` 固定为 `v2026.9.25` 并校验 SHA-256；key-cli 由该安装器选择满足要求的正式发布版
- 上游安装器会执行 Arch 的完整系统更新、编译 AUR 依赖，所需时间取决于机器和网络

## 安装

```bash
git clone https://github.com/1024971823/niri-clavis-setup.git
cd niri-clavis-setup
bash install.sh --wallpaper /绝对路径/你的壁纸.jpg
```

如果未指定壁纸，脚本会使用已有的 `~/.config/niri/wallpaper.jpg`；否则生成一张简单的渐变图。桌宠不在仓库中，如本机已有启动脚本，可以加上：

```bash
bash install.sh --wallpaper /绝对路径/壁纸.jpg \
  --pet-start /绝对路径/桌宠/start.sh \
  --pet-process-match '/绝对路径/桌宠/[p]et.js'
```

仅应用配置（已经安装上游包时）：

```bash
bash install.sh --config-only --wallpaper /绝对路径/壁纸.jpg
```

先检查模板与本机依赖，不写文件：

```bash
bash install.sh --dry-run
```

安装后退出当前会话，在登录界面选择 **Niri**。脚本不会强行重启现有桌面。

## 验证与恢复

```bash
bash verify.sh
bash restore.sh
```

`verify.sh` 会检查 Niri 配置、Clavis 原生插件及用户服务。在 Niri 会话内还检查状态栏和壁纸层。`restore.sh` 会恢复安装前备份的用户配置和服务启用状态；备份位于 `~/.local/state/niri-clavis-setup/backups/`。恢复后重新登录。

如果 Clavis 发生启动错误，原壁纸仍由 `swaybg` 显示。`Mod+D` 保留 Fuzzel 应用菜单作为后备入口，`Mod+T` 打开 Alacritty。`Super+Space` 打开 Clavis 搜索，`Mod+N` 打开信息侧栏，`Mod+A` 打开快捷设置。

## 上游与更新

Clavis Shell、key-cli、M3Shapes 和字体各有自己的许可证，本仓库不复制它们的代码或素材。Niri 配置模板参考了 Niri 默认配置，原项目许可证以其仓库为准。上游安装器的包格式、依赖或服务名变化时，需要更新本脚本中的发布版本、校验值和兼容处理，再重新验证安装。

当前版本针对 Arch pacman 7.1 的 `pacman -Qp --print-format` 不兼容，安装过程中只对这个只读查询提供本地兼容命令。Clavis 包中的 QML 插件还需要同目录动态库，本仓库用用户服务 drop-in 设定插件目录；不修改 pacman 管理的文件。
