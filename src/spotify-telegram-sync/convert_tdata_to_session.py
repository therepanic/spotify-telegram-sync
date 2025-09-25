from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.api import API, UseCurrentSession
import asyncio

def convert(session_path, tdata_path):
    tdesk = TDesktop(tdata_path)
    api = API.TelegramIOS.Generate()
    return asyncio.run(tdesk.ToTelethon(session_path, UseCurrentSession, api))
