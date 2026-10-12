# Niri + Clavis 桌面配置

这是从我的 Arch Linux 桌面整理出的 Niri + [Clavis Shell](https://github.com/StatIndet/quickshell) 配置与安装脚本。包含 Niri 键位、Clavis 的个性化设置、中文 Fuzzel、Alacritty 终端主题、轻量 Bash Git 提示符、交互式目录选择、壁纸兜底，以及 Clavis 原生 QML 插件的库路径修复。

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

终端使用与 Neovim 相同的 JetBrainsMono Nerd Font（字号 14）、统一的半透明深色背景、柔和阴影和双行 Bash 提示符。Alacritty 启动后自动进入 tmux 多终端界面，最顶端有一条白色像素渐变，下面是终端标签栏：当前标签浅蓝高亮并带蓝点，其他标签保持深色。提示符左下角用 Arch Linux 图标显示当前目录；进入 Git 仓库后还会显示分支、`+N` 已暂存、`~N` 未暂存、`?N` 未跟踪、`!N` 冲突、`⇡N` 领先远端和 `⇣N` 落后远端，干净仓库显示 `✓`。不需要安装 Starship。已有 Bash 设置会保留；重新打开 Alacritty，或在当前终端执行 `source ~/.bashrc` 即可看到提示符。

Niri 窗口式终端多开：`Super+T` 新建终端窗口，`Super+Tab` / `Super+Shift+Tab` 在窗口之间循环切换，`Super+,` 把右侧终端并入当前窗口组，`Super+W` 在普通平铺和多窗口标签显示之间切换，`Super+K` / `Super+J` 在标签内上下切换，`Super+.` 把底部终端拆分回独立窗口，`Super+O` 查看所有终端。

终端内标签多开：`Ctrl+B` 再按 `C` 新建标签，`Ctrl+B` 再按 `Tab` / `N` / `P` 或左右方向键切换标签，`Ctrl+B` 再按数字键直接跳转，`Ctrl+B` 再按 `Q` 显示标签列表，`Ctrl+B` 再按 `,` 重命名，`Ctrl+B` 再按 `X` 关闭当前标签；也可以用 `Alt+1` 到 `Alt+9` 直接切换。多个独立终端窗口用 `Super+T`（或 `Super+Enter`）创建，`Mod+O` 打开 Niri 多窗口概览。

单独输入 `cd` 会打开交互式目录选择器：上下键选择，左键返回上一级继续选择，右键进入所选目录继续选择，回车最终进入，`Esc` 取消；也可以使用 `cd -i` 主动打开。输入 `cd /路径`、`cd ..`、`cd -` 时保持 Bash 原有行为。该选择器使用 `fzf`，安装脚本会自动补齐这个依赖。

## 验证与恢复

```bash
bash verify.sh
bash restore.sh
```

`verify.sh` 会检查 Niri 配置、Clavis 原生插件及用户服务。在 Niri 会话内还检查状态栏和壁纸层。`restore.sh` 会恢复安装前备份的用户配置和服务启用状态；备份位于 `~/.local/state/niri-clavis-setup/backups/`。恢复后重新登录。

如果 Clavis 发生启动错误，原壁纸仍由 `swaybg` 显示。`Mod+D` 保留 Fuzzel 应用菜单作为后备入口，`Mod+T` 新建 Alacritty 终端窗口，窗口焦点框使用白色到浅蓝的渐变。`Super+Space` 打开 Clavis 搜索，`Mod+N` 打开信息侧栏，`Mod+A` 打开快捷设置。

## 上游与更新

Clavis Shell、key-cli、M3Shapes 和字体各有自己的许可证，本仓库不复制它们的代码或素材。Niri 配置模板参考了 Niri 默认配置，原项目许可证以其仓库为准。上游安装器的包格式、依赖或服务名变化时，需要更新本脚本中的发布版本、校验值和兼容处理，再重新验证安装。

当前版本针对 Arch pacman 7.1 的 `pacman -Qp --print-format` 不兼容，安装过程中只对这个只读查询提供本地兼容命令。Clavis 包中的 QML 插件还需要同目录动态库，本仓库用用户服务 drop-in 设定插件目录；不修改 pacman 管理的文件。
