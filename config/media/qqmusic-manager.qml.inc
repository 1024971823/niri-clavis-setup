    // QQ Music 1.1.8 sends title/artist but omits MPRIS artwork.
    property var qqMusicArtwork: ({})
    FileView {
        id: qqMusicArtworkFile
        path: Paths.cacheHome + "/qqmusic-artwork.json"
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                root.qqMusicArtwork = JSON.parse(qqMusicArtworkFile.text()).players || {};
            } catch (error) {
                root.qqMusicArtwork = {};
            }
        }
    }

    function artworkFor(player) {
        if (!player)
            return "";
        if (player.trackArtUrl)
            return player.trackArtUrl;
        const entry = root.qqMusicArtwork[player.dbusName];
        if (!entry || entry.title !== player.trackTitle || entry.album !== player.trackAlbum)
            return "";
        const artists = player.metadata["xesam:artist"] || [];
        if (JSON.stringify(entry.artists) !== JSON.stringify(artists))
            return "";
        return entry.artUrl || "";
    }
