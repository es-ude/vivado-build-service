import tomli


class Config:
    def __init__(self, config_file_path='docs/config.toml'):
        with open(config_file_path, 'rb') as f:
            config_dict = tomli.load(f)
            self.config = config_dict

    def get(self):
        return self.config
