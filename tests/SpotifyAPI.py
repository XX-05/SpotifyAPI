from API import SpotifyAPI


api = SpotifyAPI()
api.load_credentials_from_file("credentials.json")

song = api.get_track_info("2kWowW0k4oFymhkr7LmvzO?si=dIOC6pQZR2mg-gqXyYFgLw", as_object=True)
song.download(try_lyrics=True)
