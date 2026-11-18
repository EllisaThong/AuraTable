"""Optional local audio. Press M to mute. Replace generated WAVs with your recordings."""
from pathlib import Path
import arcade

class AudioManager:
    def __init__(self):
        self.muted = False
        self.sounds = {}
        self.players = []
        self.unavailable = set()
        self.music = None
        self.music_player = None

    def play(self, name):
        if self.muted or name in self.unavailable:
            return
        path = Path(__file__).resolve().parent / 'audio' / (name + '.wav')
        if not path.exists():
            return
        try:
            if name not in self.sounds:
                self.sounds[name] = arcade.load_sound(str(path))
            self.players = [(sound, player) for sound, player in self.players if player.playing]
            sound = self.sounds[name]
            volume = 0.15 if name == "wash" else 0.35
            player = sound.play(volume=volume)
            if player is not None:
                self.players.append((sound, player))
        except Exception as exc:
            self.unavailable.add(name)
            print(f'Audio unavailable ({name}): {exc}')

    def start_music(self):
        if self.muted or self.music_player is not None:
            return
        path = Path(__file__).resolve().parent / "audio" / "background.wav"
        if not path.exists():
            return
        try:
            self.music = arcade.load_sound(str(path))
            self.music_player = self.music.play(volume=.12, loop=True)
        except Exception as exc:
            print(f"Background audio unavailable: {exc}")

    def toggle(self):
        self.muted = not self.muted
        if self.muted:
            if self.music_player is not None:
                self.music.stop(self.music_player)
                self.music_player = None
            for sound, player in self.players:
                try:
                    sound.stop(player)
                except Exception:
                    pass
            self.players.clear()
        else:
            self.start_music()
        print('Audio muted' if self.muted else 'Audio enabled')

audio = AudioManager()
