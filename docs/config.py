import configparser

config_file_path = 'docs/config.ini'

class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(config_file_path)

    def get(self):
        return {
            # Paths
            'send': self.config.get('Paths', 'send'),
            'receive': self.config.get('Paths', 'receive'),
            'request': self.config.get('Paths', 'request'),

            # Connection
            'host': self.config.get('Connection', 'host'),
            'port': self.config.getint('Connection', 'port'),
            'chunk size': self.config.getint('Connection', 'chunk size'),
            'delimiter': self.config.get('Connection', 'delimiter'),

            # VNC
            'username': self.config.get('VNC', 'username'),
            'ip address': self.config.get('VNC', 'ip address')
        }
