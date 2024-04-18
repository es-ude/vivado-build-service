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
            'tcl script': self.config.get('Paths', 'tcl script'),
            'bash script': self.config.get('Paths', 'bash script'),
            'constraints': self.config.get('Paths', 'constraints'),

            # Connection
            'host': self.config.get('Connection', 'host'),
            'port': self.config.getint('Connection', 'port'),
            'chunk size': self.config.getint('Connection', 'chunk size'),
            'delimiter': self.config.get('Connection', 'delimiter'),

            # VNC
            'username': self.config.get('VNC', 'username'),
            'ip address': self.config.get('VNC', 'ip address'),

            # Database
            'DB URL': self.config.get('Database', 'DB URL'),

            # Debug
            'debug user': self.config.get('Debug', 'debug user'),
            'example build': self.config.get('Debug', 'example build'),

            # Tests
            'test bash script': self.config.get('Tests', 'test bash script'),
            'test packet': self.config.get('Tests', 'test packet')
        }
