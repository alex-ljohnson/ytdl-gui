"""Extension classes for spotify"""

import re

import spotipy
import validators

from modules.extension import PlatformExtension
from modules.utils import log_debug, relative_data


class SpotifyExtension(PlatformExtension):
    """Provides an extension hook for spotify"""

    _name = "Spotify url support"
    _REQUIRED_PACKAGES = {"spotipy", "validators"}

    def __init__(self):
        super().__init__()
        self.PKCE_man = None  # pylint: disable=C0103
        self.cache: spotipy.CacheFileHandler | None = None
        self.spotify: spotipy.Spotify | None = None

    def enable(self):
        super().enable()
        token = relative_data(".tokencache", False)
        self.cache = spotipy.CacheFileHandler(token)
        self.PKCE_man = spotipy.SpotifyPKCE(
            redirect_uri="http://localhost:8000/authorise",
            client_id="fbeffc75e6a44a119e33e9061123fefc",
            scope="playlist-read-private,playlist-read-collaborative",
            cache_handler=self.cache,
        )
        self.spotify = spotipy.Spotify(auth_manager=self.PKCE_man)

    def disable(self):
        super().disable()
        self.spotify = None
        self.PKCE_man = None

    def check_type(self, item: str) -> bool:
        return (bool(validators.url(item)) and "open.spotify.com" in item) or bool(
            re.fullmatch(
                r"spotify:((track)|(playlist)|(album)|(artist)|(show)|(episode)):([0-9]|[A-Z]|[a-z]){22}", item
            )
        )

    def get_items(self, urn) -> list[str] | None:
        """This gathers items to be downloaded based on the specified search query or url (youtube and spotify only)
        <search> May be a search query for youtube e.g. 'Smash mouth All star' or a youtube/spotify url e.g. 'https://open.spotify.com/track/3cfOd4CMv2snFaKAnMdnvK?si=Ig6gRcMRS_aK7qMasRM0AQ' or 'https://open.spotify.com/playlist/4O9mmcH1OQ9azGfJPe4lMn?si=CwFHUVWxTXO8nkE9swBl0A'
        Accepts: [youtube or spotify urls, youtube searches]
        URL types: [spotify track, playlist, artist, album, podcast episode or podcast show urls]
        Returns: None for errors or the list of search queries"""

        if not self.ready or not self.spotify:
            return None
        if "spotify.com" in urn:
            log_debug("Is spotify url")
            if "track" in urn:
                try:
                    results = self.spotify.track(urn, market="from_token")
                    if not results:
                        return None
                except spotipy.SpotifyException:
                    print(f"Couldn't find the requested track (Invalid track url/uri - {urn})")
                else:
                    return [f"{results['name']} {results['artists'][0]['name']}"]

            elif "playlist" in urn:
                tracks = []
                try:
                    results = self.spotify.playlist_items(
                        urn, fields="items(track),total,limit,next", market="from_token"
                    )
                    if results:
                        tracks = [
                            f"{track['track']['name']} {track['track']['artists'][0]['name']}"
                            for track in results["items"]
                        ]
                        nxt = results["next"]
                        while nxt:
                            results = self.spotify.next(results)
                            if results:
                                tracks.extend(
                                    [
                                        f"{track['track']['name']} {track['track']['artists'][0]['name']}"
                                        for track in results["items"]
                                    ]
                                )
                                nxt = results["next"]
                        return tracks
                except spotipy.SpotifyException as ex:
                    print(f"Couldn't find the requested playlist (Invalid playlist url/uri - {urn})\n{ex}")

            elif "artist" in urn:
                try:
                    results = self.spotify.artist_top_tracks(urn, country="from_token")
                    if results:
                        return [f"{track['name']} {track['artists'][0]['name']}" for track in results["tracks"]]
                except spotipy.SpotifyException:
                    print(f"Couldn't find the requested artist (Invalid artist url/uri - {urn})")
            elif "album" in urn:
                try:
                    results = self.spotify.album_tracks(urn, market="from_token")
                    if results:
                        return [f"{track['name']} {track['artists'][0]['name']}" for track in results["items"]]
                except spotipy.SpotifyException:
                    print(f"Couldn't find the requested album (Invalid album url/uri - {urn})")
            elif "episode" in urn:
                try:
                    results = self.spotify.episode(urn)
                    if results:
                        return [f"{results['name']} {results['show']['name']}"]
                except spotipy.SpotifyException:
                    print(
                        f"Couldn't find the requested episode (Invalid episode url/uri - {urn})\nOr Episode wasn't available in your market."
                    )
            elif "show" in urn:
                try:
                    results = self.spotify.show(urn)
                    if results:
                        return [f"{episode['name']} {results['name']}" for episode in results["episodes"]["items"]]
                except spotipy.SpotifyException:
                    print(f"Couldn't find the requested show (Invalid show url/uri - {urn})")

        else:
            print("Invalid url")
            return None
        return None
