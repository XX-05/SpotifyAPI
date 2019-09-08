import os

import json
import socket
import random
import requests


class SpotifyAPI:
    def __init__(self):
        self.credentials = {
            "client_id" : None,
            "response_type": None,
            "redirect_uri": None,
            "state": random.random() * 100,
            "scopes": None,
        }

    def load_credentials_from_file(self, credentials_file):
        if not os.file.exists(credentials_file):
            raise FileNotFoundError("credentials file %s does not exist!" % credentials_file)

        with open(credentials_file, "r") as f:
            credentials = json.load(f)

        print(credentials)

    def load_credentials(self, client_id, client_secret, redirect_uri, scopes=None):
        print("hi")