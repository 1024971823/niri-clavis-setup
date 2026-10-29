# Niri + Clavis 桌面配置

这是从我的 Arch Linux 桌面整理出的 Niri + [Clavis Shell](https://github.com/StatIndet/quickshell) 配置与安装脚本。包含 Niri 键位、Clavis 的个性化设置、中文 Fuzzel、Kitty 终端主题、轻量 Bash Git 提示符、交互式目录选择、带实时预览的 Bash 指令补全、壁纸兜底，以及 Clavis 原生 QML 插件的库路径修复。

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

终端使用与 Neovim 相同的 JetBrainsMono Nerd Font（字号 14）、统一的半透明深色背景、柔和阴影和双行 Bash 提示符。Kitty 启动后自动进入 tmux 多终端界面，最顶端有一条白色像素渐变，下面是终端标签栏：当前标签浅蓝高亮并带蓝点，其他标签保持深色。Kitty 保留流畅的光标拖尾动画，并继续使用与 Alacritty 相同的字体、色彩、透明度和内边距。提示符左下角用 Arch Linux 图标显示当前目录；进入 Git 仓库后还会显示分支、`+N` 已暂存、`~N` 未暂存、`?N` 未跟踪、`!N` 冲突、`⇡N` 领先远端和 `⇣N` 落后远端，干净仓库显示 `✓`。不需要安装 Starship。已有 Bash 设置会保留；重新打开 Kitty，或在当前终端执行 `source ~/.bashrc` 即可看到提示符。

Niri 窗口式终端多开：`Super+T` 新建终端窗口，`Super+Tab` / `Super+Shift+Tab` 在窗口之间循环切换，`Super+,` 把右侧终端并入当前窗口组，`Super+W` 在普通平铺和多窗口标签显示之间切换，`Super+K` / `Super+J` 在标签内上下切换，`Super+.` 把底部终端拆分回独立窗口，`Super+O` 查看所有终端。

Kitty 标签：`Ctrl+Shift+T` 新建标签，`Ctrl+Shift+Right` / `Ctrl+Shift+Left` 切换标签。每个 Kitty 标签会启动一个 tmux 会话；底部标题随当前程序和所在目录更新，例如 `omp · 项目名`、`nvim · 项目名`。tmux 内部标签也会自动显示当前程序名，手动重命名后保留自定义名称。

终端内标签多开：`Ctrl+B` 再按 `C` 新建标签，`Ctrl+B` 再按 `Tab` / `N` / `P` 或左右方向键切换标签，`Ctrl+B` 再按数字键直接跳转，`Ctrl+B` 再按 `Q` 显示标签列表，`Ctrl+B` 再按 `,` 重命名，`Ctrl+B` 再按 `X` 关闭当前标签；也可以用 `Alt+1` 到 `Alt+9` 直接切换。多个独立终端窗口用 `Super+T`（或 `Super+Enter`）创建，`Mod+O` 打开 Niri 多窗口概览。

终端会边输入边显示淡色的完整补全建议，约 0.16 秒后自动列出命令、函数、命令参数、可执行项或路径候选，候选菜单带简短说明；从预览补全中选完一条后会继续提示下一段内容。按 `→`、`End` 或 `Ctrl+F` 接受整条建议，`Alt+→` 或 `Alt+F` 只接受一个词；候选出现后用 `Tab`、上下键选择，回车插入，`Esc` 取消。输入 `git st`、`sys` 或函数名前几个字母即可看到效果。

仍可按 `Ctrl+Space`（或 `Alt+/`）打开大窗口指令预览补全：命令位置会列出可执行命令，参数位置会列出文件、目录、变量和命令选项；右侧实时显示命令帮助、文件内容或目录列表，上下键选择后回车插入，`Esc` 取消。

单独输入 `cd` 会打开交互式目录选择器：上下键选择，左键返回上一级继续选择，右键进入所选目录继续选择，回车最终进入，`Esc` 取消；也可以使用 `cd -i` 主动打开。输入 `cd /路径`、`cd ..`、`cd -` 时保持 Bash 原有行为。该选择器使用 `fzf`，安装脚本会自动补齐这个依赖。

交互式 `ssh 用户@主机` 会把同一套目录选择和指令补全带到对方的 bash，不修改对方的 `~/.bashrc`。对方原有登录配置会先加载。`ssh 主机 命令` 和 `ssh -T git@github.com` 仍是原来的 SSH。对方需要 bash；没有 `fzf` 时目录菜单和预览补全不可用，登录本身不受影响。需要原来的 SSH 客户端时执行 `command ssh`。

## 胶囊通知与 QQ 音乐封面

安装时会屏蔽当前用户的 `mako.service`，防止它通过 D-Bus 自动启动并抢占通知服务。通知由 Clavis 接管，在顶部胶囊显示；恢复脚本会还原此前的 Mako 配置和运行状态。

QQ 音乐 AppImage 1.1.8 可以通过 MPRIS 上报歌名和歌手，但没有上报封面。本适配会自动识别媒体服务对应的 QQ 音乐进程，在缺少原生封面时查询 QQ 音乐公开曲库，再把匹配的专辑封面提供给胶囊、歌词面板和锁屏媒体卡。播放器名称显示为「QQ 音乐」。首次查询可能需要几秒，切歌或退出播放器后不会沿用上一首封面；同名不同歌手、专辑不匹配或多个专辑版本无法区分时保留默认图标。原生封面始终优先。

适配不搜索或读取 QQ 音乐账号、Cookies、登录配置，也不依赖 AppImage 的安装位置、挂载目录或特定用户名。通过系统媒体接口和 `/proc` 进程信息识别播放器；仅将歌名、歌手发送给 QQ 音乐公开曲库，封面从其图片服务加载。适用于以 `qqmusic` 进程运行并提供 MPRIS 的 Linux 客户端；Wine、Flatpak 或未来客户端版本需要另行验证。

安装器自动查找用户 XDG 配置目录、运行中的 Clavis 配置和系统 XDG 配置目录；只在用户配置目录中应用 QML 适配，系统配置会复制为用户副本。辅助程序、缓存和备份分别使用 `XDG_DATA_HOME`、`XDG_CACHE_HOME`、`XDG_STATE_HOME`（未设置时使用标准用户目录），也支持 Clavis 的 `CLAVIS_CACHE_HOME`。仓库不包含本机绝对路径或 QQ 音乐私有配置。现有整套桌面安装脚本仍遵循前文约定使用标准用户目录；这些 XDG 支持专用于本节集成。

已有桌面可单独安装本功能，无需覆盖整套 Niri 配置：

```bash
sudo pacman -S --needed python-gobject
python3 scripts/install_media.py --dry-run
python3 scripts/install_media.py
```

会短暂重启正在运行的 Clavis。卸载本次集成、恢复安装前状态：

```bash
python3 scripts/install_media.py --restore
```

检查运行情况：

```bash
systemctl --user status clavis-qqmusic-artwork.service
playerctl -l
```

该适配需要访问 QQ 音乐公开曲库；网络错误或曲库接口变化时会保留默认封面并稍后重试。Clavis 更新若覆盖用户 QML，请重新运行单独安装命令；遇到不支持的 QML 结构会在写入前报错。

## 验证与恢复

```bash
bash verify.sh
bash restore.sh
```

`verify.sh` 会检查 Niri 配置、Clavis 原生插件及用户服务。在 Niri 会话内还检查状态栏和壁纸层。`restore.sh` 会恢复安装前备份的用户配置和服务启用状态；备份位于 `~/.local/state/niri-clavis-setup/backups/`。恢复后重新登录。

如果 Clavis 发生启动错误，原壁纸仍由 `swaybg` 显示。`Mod+D` 保留 Fuzzel 应用菜单作为后备入口，`Mod+T` 新建 Kitty 终端窗口，窗口焦点框使用白色到浅蓝的渐变。`Super+Space` 打开 Clavis 搜索，`Mod+N` 打开信息侧栏，`Mod+A` 打开快捷设置。

## 上游与更新

Clavis Shell、key-cli、M3Shapes 和字体各有自己的许可证，本仓库不复制它们的代码或素材。Niri 配置模板参考了 Niri 默认配置，原项目许可证以其仓库为准。上游安装器的包格式、依赖或服务名变化时，需要更新本脚本中的发布版本、校验值和兼容处理，再重新验证安装。

当前版本针对 Arch pacman 7.1 的 `pacman -Qp --print-format` 不兼容，安装过程中只对这个只读查询提供本地兼容命令。Clavis 包中的 QML 插件还需要同目录动态库，本仓库用用户服务 drop-in 设定插件目录；不修改 pacman 管理的文件。
