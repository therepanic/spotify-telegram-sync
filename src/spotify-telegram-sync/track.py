class Track:
    def __init__(self, name, artists, cover_url, album, spotify_url):
        self.name = name
        self.artists = artists
        self.cover_url = cover_url
        self.album = album
        self.spotify_url = spotify_url

    def __eq__(self, other):
        return isinstance(other, Track) and self.name == other.name and self.artists == other.artists and self.cover_url == other.cover_url and self.album == other.album and self.spotify_url == other.spotify_url

    def __hash__(self):
        return hash((self.name, self.artists, self.cover_url, self.album, self.spotify_url))
