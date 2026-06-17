import datetime
from dataclasses import dataclass

@dataclass
class Playlist:
    id: str
    name: str
    url: str
    lastSync: datetime.time