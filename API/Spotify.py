import os

import time
import json
import random
import base64

import urllib
import requests
import webbrowser

from .SocketServer import SocketServer
from .SpotifyObjects import SpotifyPlaylist, SpotifyTrack


class SpotifyOAuthError(Exception):
    pass


class SpotifyAPIAccessError(Exception):
    pass


class SpotifyAPI:
    def __init__(self):
        self.credentials = {
            "client_id": None,
            "client_secret": None,
            "response_type": "code",
            "redirect_uri": "http://127.0.0.1:42069",
            "state": random.random() * 100,
            "scope": None,
        }

        self.auth_header = None
        self.token_info = self._load_stored_info("SPOTIFY_TOKEN_INFO")

    def _load_stored_info(self, name):
        file_name = base64.b64encode(name.encode("ascii"))
        file_name = ".cache-%s" % file_name.decode("ascii")

        if not os.path.isfile(file_name):
            return None

        with open(file_name, "r") as f:
            data = base64.b64decode(f.read().encode("ascii")).decode("ascii")
            return json.loads(data)

    def _store_info(self, data, name):
        file_name = base64.b64encode(name.encode("ascii"))
        file_name = ".cache-%s" % file_name.decode("ascii")

        with open(file_name, "w") as f:
            data = str(data).replace("\'", "\"").encode("ascii")
            f.write(base64.b64encode(data).decode("ascii"))

    def load_credentials_from_file(self, credentials_file):
        if not os.path.isfile(credentials_file):
            raise FileNotFoundError("credentials file '%s' does not exist!" % credentials_file)

        with open(credentials_file, "r") as f:
            credentials = json.load(f)

        if not ("client_id" in credentials):
            raise SpotifyOAuthError("invalid credentials file: no client_id provided")
        elif not ("client_secret" in credentials):
            raise SpotifyOAuthError("invalid credentials file: no client_secret provided")

        self.credentials["client_id"] = credentials["client_id"]
        self.credentials["client_secret"] = credentials["client_secret"]

        if "redirect_uri" not in credentials:
            self.credentials["redirect_uri"] = credentials["redirect_uri"]

        if "scope" in credentials:
            self.credentials["scope"] = credentials["scope"]

        self.authenticate()

    def load_credentials(self, client_id, client_secret, redirect_uri=None, scopes=None):
        self.credentials["client_id"] = client_id
        self.credentials["client_secret"] = client_secret

        if redirect_uri is not None:
            self.credentials["redirect_uri"] = redirect_uri

        self.credentials["scope"] = scopes

        self.authenticate()

    def _listen_for_auth_code(self):
        port = self.credentials["redirect_uri"].split(":")
        port = int(port[-1])

        ss = SocketServer("", port)
        data = str(ss.listen())

        parameters = data.split("\n")[0].split("?")[1].split(" ")[0].split("&")
        parameters = {i.split("=")[0]: i.split("=")[1] for i in parameters}

        return parameters

    def _encode_uri(self, base, data):
        return f"{base}?{urllib.parse.urlencode(data)}"

    def _refresh_auth_header(self, token_info):
        return {"Authorization": "Bearer %s" % token_info["access_token"]}

    def _make_auth_header(self, client_id, client_secret):
        b64 = (client_id + ":" + client_secret)
        b64 = base64.b64encode(b64.encode("ascii"))

        return {"Authorization": "Basic %s" % b64.decode("ascii")}

    def _modify_token_expiration(self, token):
        token["expires_in"] = token["expires_in"] + time.time()
        return token

    def _request_access_token(self, access_code):
        body = {
            "grant_type": "authorization_code",
            "code": access_code,
            "redirect_uri": self.credentials["redirect_uri"]
        }
        
        auth_header = self._make_auth_header(self.credentials["client_id"], self.credentials["client_secret"])
        response = requests.post("https://accounts.spotify.com/api/token", data=body, headers=auth_header)

        if response.status_code != 200:
            raise SpotifyOAuthError("error requesting access token '%s'" % response.reason)

        token_info = response.json()
        token_info = self._modify_token_expiration(token_info)

        self.auth_header = self._refresh_auth_header(token_info)
        self._store_info(token_info, "SPOTIFY_TOKEN_INFO")

        self.token_info = token_info

        return token_info

    def _refresh_access_token(self, token_info):
        body = {
            "grant_type": "refresh_token",
            "refresh_token": self.token_info["refresh_token"]
        }

        header = self._make_auth_header(self.credentials["client_id"], self.credentials["client_secret"])
        response = requests.post("https://accounts.spotify.com/api/token", body, headers=header)

        if response.status_code != 200:
            raise SpotifyOAuthError("error refreshing access token '%s'" % response.reason)

        rf_token_info = response.json()
        rf_token_info = self._modify_token_expiration(rf_token_info)

        if "refresh_token" not in rf_token_info:
            rf_token_info["refresh_token"] = token_info["refresh_token"]

        self.auth_header = self._refresh_auth_header(rf_token_info)
        self._store_info(rf_token_info, "SPOTIFY_TOKEN_INFO")

        self.token_info = rf_token_info

        return rf_token_info

    def _is_token_expired(self, token_info):
        return token_info["expires_in"] - int(time.time()) < 60

    def authenticate(self):
        token_info = self._load_stored_info("SPOTIFY_TOKEN_INFO")

        if not token_info:
            base_url = "https://accounts.spotify.com/authorize"

            credentials = self.credentials.copy()

            if credentials["scope"] is None:
                credentials.pop("scope")

            url = self._encode_uri(base_url, credentials)
            webbrowser.open_new_tab(url)

            parameters = self._listen_for_auth_code()

            if float(parameters["state"]) != self.credentials["state"]:
                raise SpotifyOAuthError("unable to verify authenticity of returned access code (unmaching state)")

            if "error" in parameters:
                raise SpotifyOAuthError("error obtaining access code")

            token_info = self._request_access_token(parameters["code"])

            return token_info

        elif self._is_token_expired(token_info):
            self._refresh_access_token(token_info)

    def access_api(self, uri, body=None, request_type="GET", token_refreshed=False):
        if self._is_token_expired(self.token_info):
            self.token_info = self._refresh_access_token(self.token_info)

        if request_type not in ["GET", "POST"]:
            raise SpotifyAPIAccessError(f"Bad Request Type: {request_type}")

        if request_type == "POST" and body:
            response = requests.post(uri, data=body, headers=self.auth_header)
        elif request_type == "GET":
            response = requests.get(uri, headers=self.auth_header)
        else:
            raise Exception("request type (%s) not valid" % request_type)

        if response.status_code != 200:
            if response.status_code == 401 and not token_refreshed:
                self.token_info = self._refresh_access_token(self.token_info)
                return self.access_api(uri, body, request_type, token_refreshed=True)
            else:
                raise SpotifyAPIAccessError(response.reason)

        return response.json()

    def get_track_info(self, track_id, as_object=False):
        uri = f"https://api.spotify.com/v1/tracks/{track_id}"
        info = self.access_api(uri)

        if as_object:
            return SpotifyTrack(info)

        return info

    def get_playlist_info(self, playlist_id, as_object=False):
        uri = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        info = self.access_api(uri)

        if as_object:
            return SpotifyPlaylist(info, self)

        return info
