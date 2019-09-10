from API import SpotifyAPI


api = SpotifyAPI()
api.load_credentials_from_file("credentials.json")

api.authenticate()
