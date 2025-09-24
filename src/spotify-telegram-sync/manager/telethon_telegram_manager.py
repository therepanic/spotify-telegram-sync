from telethon.sync import TelegramClient, functions
from manager.telegram_manager import TelegramManager

class TelethonTelegramManager(TelegramManager):
    def __init__(self, session, api_id, api_hash):
        self.client = TelegramClient(session, api_id, api_hash)
    
    def start(self):
        return self.client.start()

    def upload_file(self, file_path):
        return self.client.upload_file(file_path)

    def save_music(self, id, unsave, after_id):
        return self.client(functions.account.SaveMusicRequest(id, unsave, after_id))

    def send_file(self, peer, file):
        return self.client.send_file(peer, file)
    
    def delete_message(self, peer, msg):
        return self.client.delete_messages(peer, msg)

