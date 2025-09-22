from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = int(capacity)
        self.cache = OrderedDict()

    def __contains__(self, key):
        return key in self.cache

    def __len__(self):
        return len(self.cache)

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key, default=None):
        if key not in self.cache:
            return default
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def peek_lru(self):
        if not self.cache:
            return None
        key = next(iter(self.cache))
        return key, self.cache[key]

    def pop_lru(self):
        if not self.cache:
            return None
        key, value = self.cache.popitem(last=False)
        return key, value

    def is_full(self):
        return len(self.cache) >= self.capacity

    def __iter__(self):
        return iter(self.cache)
