from abc import ABC, abstractmethod

class TelegramManager(ABC):

    @abstractmethod
    def start(self):
        self.client.start()
