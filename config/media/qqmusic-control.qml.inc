    // QQ Music reports CanControl=false even when its control methods work.
    Process {
        id: qqMusicControl
        stderr: StdioCollector {
            onStreamFinished: if (text.trim()) console.warn("QQ Music control:", text.trim())
        }
    }

    function control(player, action) {
        if (!player)
            return;
        if (root.qqMusicArtwork[player.dbusName]) {
            if (!qqMusicControl.running) {
                const method = action === "PlayPause" ? (player.isPlaying ? "Pause" : "Play") : action;
                qqMusicControl.exec(["/usr/bin/python3",
                                     Paths.xdgDataHome + "/niri-clavis-setup/qqmusic-artwork.py",
                                     "--player", player.dbusName, "--control", method]);
            }
            return;
        }
        if (action === "Previous")
            player.previous();
        else if (action === "Next")
            player.next();
        else if (action === "PlayPause")
            player.togglePlaying();
    }

    function canToggle(player) {
        return player && (player.canTogglePlaying || !!root.qqMusicArtwork[player.dbusName]);
    }
