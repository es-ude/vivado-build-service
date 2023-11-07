import configparser

config_file_path = 'docs/config.ini'

class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(config_file_path)

    def get(self):
        return {
            'host': self.config.get('Connection', 'host'),
            'port': self.config.getint('Connection', 'port'),
            'chunk size': self.config.getint('Connection', 'chunk size'),
            'delimiter': self.config.get('Connection', 'delimiter'),

            'send': self.config.get('Paths', 'send'),
            'receive': self.config.get('Paths', 'receive'),
            'request': self.config.get('Paths', 'request')
        }
