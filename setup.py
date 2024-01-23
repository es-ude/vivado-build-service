from src.filehandler import reset, dos2unix, bash_script
import os

current_permissions = os.stat(bash_script + 'unix.sh').st_mode
new_permissions = current_permissions | 0o111

os.chmod(bash_script + 'unix.sh', new_permissions)
dos2unix()
reset()
