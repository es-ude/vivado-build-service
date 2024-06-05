import tomli

config_file_path = 'docs/config.toml'


class Config:
    def __init__(self):
        with open(config_file_path, 'rb') as f:
            config_dict = tomli.load(f)

        for key, value in config_dict.items():
            key.replace(' ', '_')

        self.config = config_dict

    def get(self):
        return self.config
