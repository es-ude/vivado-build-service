from src.filehandler import reset, dos2unix, bash_script
import os

bash_dir = 'scripts/bash'

for root, dirs, files in os.walk(bash_dir):
    for file in files:
        filepath = os.path.join(root, file)
        if file.split('_')[-1] == 'dos.sh':
            fname = os.path.join(bash_dir, file.split('_')[0])
            dos2unix(filepath, fname + '_unix.sh')

        current_permissions = os.stat(filepath).st_mode
        new_permissions = current_permissions | 0o111
        os.chmod(filepath, new_permissions)

reset()
