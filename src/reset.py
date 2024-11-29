from src.filehandler import delete_directories_in, clear, move_log_and_jou_files


def reset_environment():
    delete_directories_in("tmp/client")
    delete_directories_in("tmp/server")
    delete_directories_in("tests/testing-environment/tmp/client")
    delete_directories_in("tests/testing-environment/tmp/server")
    clear("tests/download")


def main():
    reset_environment()
    move_log_and_jou_files(origin="..", destination="log")


if __name__ == '__main__':
    main()
