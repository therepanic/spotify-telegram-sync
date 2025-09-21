from telethon.sync import TelegramClient
from telegram_manager import TelegramManager

class TelethonTelegramManager(TelegramManager):
    def __init__(self, session, api_id, api_hash):
        self.client = TelegramClient(session, api_id, api_hash)
    
    def start(self):
        self.client.start()
