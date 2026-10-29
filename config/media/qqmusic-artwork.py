#!/usr/bin/env python3
"""Fill missing QQ Music artwork using its public catalogue, without account data."""
import html
import argparse
import json
import os
from pathlib import Path
import re
import time
import unicodedata
import urllib.parse
import urllib.request

from gi.repository import Gio, GLib

CACHE = Path(os.environ.get("CLAVIS_CACHE_HOME") or
             str(Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "clavis"))
OUTPUT = CACHE / "qqmusic-artwork.json"


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFKC", html.unescape(value)).casefold()
                   if c.isalnum())


def choose_cover(songs, title, artists, album):
    """Require matching title and artists; reject ambiguous album versions."""
    matches = []
    wanted = {normalized(a) for a in artists if normalized(a)}
    if not normalized(title) or not wanted:
        return ""
    for song in songs:
        singers = {normalized(s.get("name", "")) for s in song.get("singer", [])}
        if normalized(song.get("songname", "")) != normalized(title) or not wanted <= singers:
            continue
        if album and normalized(song.get("albumname", "")) != normalized(album):
            continue
        mid = song.get("albummid", "")
        if re.fullmatch(r"[A-Za-z0-9]{8,32}", mid):
            matches.append(mid)
    mids = set(matches)
    if len(mids) != 1:
        return ""
    return "https://y.gtimg.cn/music/photo_new/T002R500x500M000" + mids.pop() + ".jpg"


def lookup(title, artists, album):
    query = urllib.parse.urlencode({"w": " ".join([title, *artists]),
                                  "format": "json", "p": 1, "n": 15})
    request = urllib.request.Request(
        "https://c.y.qq.com/soso/fcgi-bin/client_search_cp?" + query,
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://y.qq.com/"})
    with urllib.request.urlopen(request, timeout=12) as response:
        data = json.loads(response.read(2 * 1024 * 1024))
    if data.get("code") != 0:
        return ""
    return choose_cover(data.get("data", {}).get("song", {}).get("list", []),
                        title, artists, album)


class Bridge:
    def __init__(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.cache = {}
        self.previous = None

    def call(self, destination, path, interface, method, args=None):
        return self.bus.call_sync(destination, path, interface, method, args, None,
                                  Gio.DBusCallFlags.NONE, 1500, None).unpack()

    def control(self, player, action):
        if action not in ("Play", "Pause", "PlayPause", "Next", "Previous"):
            raise ValueError("Unsupported media action")
        if not player.startswith("org.mpris.MediaPlayer2."):
            raise ValueError("Not a media player")
        # Pin to the current unique owner, avoiding name reuse between checks.
        owner = self.call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                          "org.freedesktop.DBus", "GetNameOwner",
                          GLib.Variant("(s)", (player,)))[0]
        pid = self.call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                        "org.freedesktop.DBus", "GetConnectionUnixProcessID",
                        GLib.Variant("(s)", (owner,)))[0]
        if Path(f"/proc/{pid}/comm").read_text().strip().lower() != "qqmusic":
            raise ValueError("Control workaround is restricted to QQ Music")
        self.call(owner, "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player", action)

    def players(self):
        names = self.call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                          "org.freedesktop.DBus", "ListNames")[0]
        found = {}
        for name in names:
            if not name.startswith("org.mpris.MediaPlayer2."):
                continue
            try:
                pid = self.call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                                "org.freedesktop.DBus", "GetConnectionUnixProcessID",
                                GLib.Variant("(s)", (name,)))[0]
                if Path(f"/proc/{pid}/comm").read_text().strip().lower() != "qqmusic":
                    continue
                props = self.call(name, "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties",
                                  "GetAll", GLib.Variant("(s)", ("org.mpris.MediaPlayer2.Player",)))[0]
                meta = props.get("Metadata", {})
                found[name] = {"title": meta.get("xesam:title", ""),
                               "artists": list(meta.get("xesam:artist", [])),
                               "album": meta.get("xesam:album", ""),
                               "nativeArt": meta.get("mpris:artUrl", ""), "artUrl": ""}
            except (GLib.Error, OSError):
                continue
        return found

    def write(self, players):
        text = json.dumps({"players": players}, ensure_ascii=False)
        if text == self.previous:
            return
        CACHE.mkdir(parents=True, exist_ok=True)
        temporary = OUTPUT.with_suffix(".tmp")
        temporary.write_text(text)
        temporary.replace(OUTPUT)
        self.previous = text

    def tick(self):
        players = self.players()
        for record in players.values():
            key = (record["title"], tuple(record["artists"]), record["album"])
            cached = self.cache.get(key)
            if cached and cached[0] > time.monotonic():
                record["artUrl"] = cached[1]
        # Clear old song artwork before a potentially slow network request.
        self.write(players)
        for record in players.values():
            if record["nativeArt"] or not record["title"] or not record["artists"]:
                continue
            key = (record["title"], tuple(record["artists"]), record["album"])
            cached = self.cache.get(key)
            if cached and cached[0] > time.monotonic():
                continue
            try:
                art = lookup(*key)
            except Exception as error:
                print("Artwork lookup unavailable:", type(error).__name__, flush=True)
                art = ""
            if len(self.cache) >= 256:
                self.cache.pop(next(iter(self.cache)))
            self.cache[key] = (time.monotonic() + (86400 if art else 300), art)
            record["artUrl"] = art
        # Discard results if the song changed or QQ Music exited during lookup.
        current = self.players()
        for name, record in current.items():
            old = players.get(name)
            if old and all(old[k] == record[k] for k in ("title", "artists", "album")):
                record["artUrl"] = old["artUrl"]
        self.write(current)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", choices=("Play", "Pause", "PlayPause", "Next", "Previous"))
    parser.add_argument("--player")
    args = parser.parse_args()
    if bool(args.control) != bool(args.player):
        parser.error("--control and --player must be used together")
    bridge = Bridge()
    if args.control:
        bridge.control(args.player, args.control)
        raise SystemExit(0)
    while True:
        try:
            bridge.tick()
        except (GLib.Error, OSError) as error:
            print("Artwork bridge retry:", type(error).__name__, flush=True)
        time.sleep(2)
