from abc import ABC, abstractmethod

class TrackBackend(ABC):
    
    @abstractmethod
    def recreate(self, temp_path, track):
        pass
