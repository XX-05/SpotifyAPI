import os
from . import SongDL


def mkdir(path):
    if not os.path.exists(path):
        parent = os.path.abspath(os.path.join(path, os.pardir))
        mkdir(parent)

        os.mkdir(path)
        print(f"created directory {path}")


def status_bar(i, total, length=10):
    percent = round(i / total * length)

    bar = "".join("=" if i < percent else "." for i in range(length))
    bar = "".join(bar[i] if i != percent else ">" for i in range(length))

    return f"[{bar}]"


class SpotifyTrack(SongDL):
    def __init__(self, track_info):
        self.info = track_info

    def download(self, location="", filename=None, youtube_api=None, try_lyrics=False):
        try:
            if self.info:
                name = self.info["name"]

                artists = self.info["artists"]
                artists = [i["name"] for i in artists]

                if filename is None:
                    artists = "".join(f"{i}, " for i in artists)[:-2]
                    filename = f"{name} - {artists}"

                filepath = os.path.join(location, str(filename))
                if youtube_api:
                    self.api_download_song(name, artists, youtube_api, filepath)
                else:
                    self.download_song(name, artists, filepath, try_lyrics=try_lyrics)

        except Exception as e:
            filename = str(filename) + ".temp.wav"
            filepath = os.path.join(location, filename)

            if os.path.exists(filepath):
                os.remove(filepath)


class SpotifyPlaylist:
    pages_turned = 1

    def __init__(self, info, spotify_api):
        tracks = []

        if "items" in info:
            tracks = info["items"]
            self.next_page_url = info["next"]

        elif "tracks" in info:
            tracks = info["tracks"]["items"]
            self.next_page_url = info["tracks"]["next"]

        self.spotify_api = spotify_api

        self.tracks = list()

        for track_info in tracks:
            if track_info["is_local"]:
                continue

            track = track_info["track"]
            track = SpotifyTrack(track)

            self.tracks.append(track)

    def next_page(self, wait=0):
        if self.pages_turned > wait:
            if not self.next_page_url:
                return False

            info = self.spotify_api.access_api(self.next_page_url)
            self.__init__(info, self.spotify_api)
        self.pages_turned += 1

        return True

    def download(self, as_ids=False, location="", turn_pages=True, current_track=0, try_lyrics=False):
        mkdir(location)

        track_id = current_track
        for i in range(len(self.tracks)):
            print(status_bar(i, len(self.tracks), length=30), end="\r")
            filename = None

            if as_ids:
                filename = track_id

            track = self.tracks[i]
            track.download(location, filename, try_lyrics=try_lyrics)
            print(status_bar(i + 1, len(self.tracks), length=30), end="\r")

            track_id += 1

        print()

        if turn_pages:
            while self.next_page():
                self.download(as_ids, location, turn_pages, track_id, try_lyrics=try_lyrics)

    def api_download(self, as_ids=False, location="", turn_pages=True, current_track=0, yt_api=None):
        mkdir(location)

        track_id = current_track
        for track in self.tracks:
            filename = None

            if as_ids:
                filename = track_id

            track.download(location, filename, youtube_api=yt_api)
            track_id += 1

        if turn_pages:
            while self.next_page():
                self.api_download(as_ids, location, turn_pages, track_id, yt_api)
