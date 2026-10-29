import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("installer", "scripts/install_media.py")
art = load("art", "config/media/qqmusic-artwork.py")


class ArtworkTests(unittest.TestCase):
    def setUp(self):
        self.song = {"songname": "Track (Live)", "singer": [{"name": "Artist"}],
                     "albumname": "Album", "albummid": "0123456789ABCD"}

    def test_matching_rejects_wrong_artist_version_and_ambiguity(self):
        self.assertTrue(art.choose_cover([self.song], "Track (Live)", ["Artist"], "Album"))
        self.assertFalse(art.choose_cover([self.song], "Track (Live)", ["Other"], ""))
        self.assertFalse(art.choose_cover([self.song], "Track", ["Artist"], ""))
        self.assertFalse(art.choose_cover([self.song], "Track (Live)", ["Artist"], "Other"))
        duplicate = dict(self.song, albummid="ABCDEFGH012345")
        self.assertFalse(art.choose_cover([self.song, duplicate], "Track (Live)", ["Artist"], ""))

    def test_late_network_result_never_applies_to_new_track(self):
        old = {"title": "Old", "artists": ["Artist"], "album": "", "nativeArt": "", "artUrl": ""}
        new = dict(old, title="New")
        bridge = object.__new__(art.Bridge)
        bridge.cache = {}
        with patch.object(bridge, "players", side_effect=[{"qq": old}, {"qq": new}]), \
                patch.object(bridge, "write") as write, patch.object(art, "lookup", return_value="old.jpg"):
            bridge.tick()
        self.assertEqual(write.call_args.args[0]["qq"]["artUrl"], "")

    def test_native_art_does_not_trigger_search(self):
        player = {"title": "Song", "artists": ["Artist"], "album": "", "nativeArt": "native.jpg", "artUrl": ""}
        bridge = object.__new__(art.Bridge)
        bridge.cache = {}
        with patch.object(bridge, "players", return_value={"qq": player}), \
                patch.object(bridge, "write"), patch.object(art, "lookup") as lookup:
            bridge.tick()
        lookup.assert_not_called()

    def test_control_pins_owner_and_only_accepts_qqmusic(self):
        bridge = object.__new__(art.Bridge)
        with patch.object(bridge, "call", side_effect=[(":1.123",), (123,), ()]) as call, \
                patch.object(Path, "read_text", return_value="qqmusic\n"):
            bridge.control("org.mpris.MediaPlayer2.chromium.example", "Next")
        self.assertEqual(call.call_args.args, (":1.123", "/org/mpris/MediaPlayer2",
                                              "org.mpris.MediaPlayer2.Player", "Next"))
        with patch.object(bridge, "call", side_effect=[(":1.123",), (123,)]) as call, \
                patch.object(Path, "read_text", return_value="chromium\n"):
            with self.assertRaises(ValueError):
                bridge.control("org.mpris.MediaPlayer2.chromium.example", "Pause")
        self.assertEqual(call.call_count, 2)
        with self.assertRaises(ValueError):
            bridge.control("org.mpris.MediaPlayer2.chromium.example", "Quit")


class InstallTests(unittest.TestCase):
    def test_custom_xdg_directories(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/test config", "XDG_DATA_HOME": "/tmp/test data",
                                     "XDG_STATE_HOME": "/tmp/test state"}):
            config, data, state = installer.locations()
            self.assertEqual(config, Path("/tmp/test config"))
            self.assertEqual(data, Path("/tmp/test data"))
            self.assertEqual(state, Path("/tmp/test state/niri-clavis-setup/media"))

    def test_patch_original_layout_and_repeat(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / installer.MANAGER).parent.mkdir(parents=True)
            (root / installer.MANAGER).write_text('''import QtQuick
import Quickshell.Services.Mpris
Item {
    id: root
    function getIdentity(player) {
        let name = player.identity.toLowerCase();
        return player.identity;
    }
}
''')
            expressions = ['(isActive && MediaManager.active.trackArtUrl) ? MediaManager.active.trackArtUrl :\n    ""',
                           'player ? player.trackArtUrl || "" : ""',
                           '(player && player.trackArtUrl) ? player.trackArtUrl : ""']
            for relative, expression in zip(installer.VIEWS, expressions):
                path = root / relative
                path.parent.mkdir(parents=True)
                receiver = "MediaManager.active" if relative.endswith("MediaContent.qml") else "root.player"
                controls = '\n'.join(f'    function {method}() {{ {receiver}.{method}(); }}'
                                     for method in ("previous", "next", "togglePlaying"))
                path.write_text('Item {\n    property string artUrl: ' + expression + '\n' + controls + '\n}\n')
            result = installer.patch_qml(root)
            for relative, content in result.items():
                (root / relative).write_bytes(content)
            self.assertEqual(installer.patch_qml(root), result)
            path = root / installer.VIEWS[0]
            path.write_text('Item {\nproperty string newArtworkProperty: ""\n}\n')
            with self.assertRaises(RuntimeError):
                installer.patch_qml(root)

    def test_restore_preserves_service_symlinks_and_original_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state"
            backup = state / "backups/fixture"
            backup.mkdir(parents=True)
            target = Path(temporary) / "target"
            target.write_text("patched")
            link = Path(temporary) / "mako.service"
            link.symlink_to("/dev/null")
            (backup / "0").write_text("original")
            (backup / "manifest.json").write_text(json.dumps({"files": [
                {"target": str(target), "kind": "file", "backup": "0"},
                {"target": str(link), "kind": "symlink", "link": "original-unit"}],
                "overlay": False, "active": {installer.SERVICE: False, "mako.service": False}}))
            (state / "latest-backup").write_text(str(backup))
            with patch.object(installer, "systemctl") as control:
                control.return_value.returncode = 1
                installer.restore(state)
            self.assertEqual(target.read_text(), "original")
            self.assertEqual(os.readlink(link), "original-unit")
            self.assertFalse((state / "latest-backup").exists())


if __name__ == "__main__":
    unittest.main()
