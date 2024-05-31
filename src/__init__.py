import os

# os.chdir('../../vivado-test-runner')
print(os.getcwd())


from . import config as c
config = c.Config().get()
