import os

import json
import random
import urllib
import requests

from .SocketServer import SocketServer


class SpotifyAPIAccessError(Exception):
    pass


class SpotifyAPI:
    def __init__(self):
        self.credentials = {
            "client_id": None,
            "response_type": "code",
            "redirect_uri": "http://127.0.0.1:42069",
            "state": random.random() * 100,
            "scope": None,
        }

    def load_credentials_from_file(self, credentials_file):
        if not os.path.isfile(credentials_file):
            raise FileNotFoundError("credentials file '%s' does not exist!" % credentials_file)

        with open(credentials_file, "r") as f:
            credentials = json.load(f)

        if not ("client_id" in credentials):
            raise SpotifyAPIAccessError("invalid credentials file: no client_id provided")

        self.credentials["client_id"] = credentials["client_id"]

        if "redirect_uri" not in credentials:
            self.credentials["redirect_uri"] = credentials["redirect_uri"]

        if "scope" in credentials:
            self.credentials["scope"] = credentials["scope"]

    def load_credentials(self, client_id, redirect_uri=None, scopes=None):
        self.credentials["client_id"] = client_id

        if redirect_uri is not None:
            self.credentials["redirect_uri"] = redirect_uri

        self.credentials["scope"] = scopes

    def authenticate(self):
        # baseURL = "https://accounts.spotify.com/authorize"
        # credentials = self.credentials.copy()
        #
        # if credentials["scope"] is None:
        #     credentials.pop("scope")
        #
        # print("hi")

        port = self.credentials["redirect_uri"].split(":")
        port = int(port[-1])

        ss = SocketServer("", port)
        print(ss.listen())

