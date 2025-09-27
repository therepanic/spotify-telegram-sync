from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.api import API, UseCurrentSession
import asyncio

def convert(session_path, tdata_path):
    async def _convert():
        tdesk = TDesktop(tdata_path)
        api = API.TelegramIOS.Generate()
        client = await tdesk.ToTelethon(session_path, UseCurrentSession, api)
        await client.connect()
        await client.disconnect()
    asyncio.run(_convert())
