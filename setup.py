from src.filehandler import reset, dos2unix, bash_script
import os

bash_dir = 'scripts/bash'

for root, dirs, files in os.walk(bash_dir):
    for file in files:
        filepath = os.path.join(root, file)
        if file.split('_')[-1] == 'dos.sh':
            unix_file = os.path.join(bash_dir, "_".join(file.split('_')[:-1])) + '_unix.sh'
            dos2unix(filepath, unix_file)

        current_permissions = os.stat(filepath).st_mode
        new_permissions = current_permissions | 0o111
        os.chmod(filepath, new_permissions)

reset()
