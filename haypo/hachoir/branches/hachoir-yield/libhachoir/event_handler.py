class EventHandler(object):
    _instance = None

    # Singleton design pattern
    def __new__(cls):
        if cls._instance == None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        self.handlers = {}

    def connect(self, event_name, handler):
        if event_name in self.handlers:
            self.handlers[event_name].append(handler)
        else:
            self.handlers[event_name] = [handler]

    def raiseEvent(self, event_name, *args):
        if event_name not in self.handlers:
            return
        for handler in self.handlers[event_name]:
            handler(*args)

