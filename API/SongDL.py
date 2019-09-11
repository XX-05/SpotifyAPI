import re
import urllib.parse

import youtube_dl
from fuzzywuzzy import fuzz


def argmax(array):
    (max_index, max_value) = (0, 0)

    for i in range(len(array)):
        if array[i] > max_value:
            max_value = array[i]
            max_index = i

    return max_index


class SongDL:
    def _jaccard_score(self, x, y):
        x, y = set(x), set(y)

        union = x.union(y)
        intersection = x.intersection(y)

        return len(intersection) / len(union)

    def find_song(self, title, artists, try_lyrics=False):
        artists = "".join(name + " " for name in artists)[:-1]
        song = f"{title} {artists}"

        if try_lyrics:
            song += " lyrics"

        query_string = urllib.parse.urlencode({"search_query": song, "sp": "EgIQAQ%253D%253D"})

        html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
        decoded_content = html_content.read().decode()

        ids = re.findall(r"href=\"\/watch\?v=(.{11})", decoded_content)
        return f"www.youtube.com/watch?v={ids[0]}"

    def find_song_api(self, title, artists, api):
        artists = "".join(name + " " for name in artists)[:-1]

        song = f"{title} {artists}"
        results = api.search(q=song, maxResults=10, type="video")

        ids = [i["id"]["videoId"] for i in results["items"]]
        titles = [i["snippet"]["title"] for i in results["items"]]

        sims = [fuzz.WRatio(title, song) for title in titles]
        index = argmax(sims)

        return f"www.youtube.com/watch?v={ids[index]}"

    def download_song(self, title, artists, filename=0, try_lyrics=False):
        songURL = self.find_song(title, artists, try_lyrics)

        ydl_opts = {
            "outtmpl": f"{filename}.wav",
            "quiet": True,
            "no_warnings": True,

            'format': 'bestaudio/best',

            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192'
            }],

            'prefer_ffmpeg': True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([songURL])

        return f"{filename}.wav"

    def api_download_song(self, title, artists, api, filename=0):
        songURL = self.find_song_api(title, artists, api)

        ydl_opts = {
            "outtmpl": f"{filename}.wav",
            "quiet": True,
            "no_warnings": True,

            'format': 'bestaudio/best',

            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192'
            }],

            'prefer_ffmpeg': True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([songURL])

        return f"{filename}.wav"
