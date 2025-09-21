from abc import ABC, abstractmethod

class TelegramManager(ABC):

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def upload_file(self, file_path):
        pass

    @abstractmethod
    def save_music(self, id, unsave, after_id):
        pass

    @abstractmethod
    def send_file(self, peer, file):
        pass

