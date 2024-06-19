import psutil
import subprocess
import os

from dotenv import dotenv_values, load_dotenv
from holz_smb_connector import SMBConnector
from server_socket import start_server_socket

load_dotenv('.env')
config = dotenv_values(".env")

from holz_python_logger.logger import HolzLogger, logger
logger = HolzLogger(logger)


def _download_file_from_smb(filename: str):
    with SMBConnector(
        host=config['SMB_HOST'],
        username=config['SMB_USERNAME'],
        password=config['SMB_PASSWORD'],
        shared_folder=config['SMB_SHARED_FOLDER'],
        port=config['SMB_PORT'],
        work_dir=config['SMB_WORK_DIR']
    ) as smb_connector:
        disk_filename = '/'.join([config['FILES_DIR'], filename.split('/')[-1]])
        smb_path = "/".join([smb_connector.work_dir, filename])
        file_obj = open(disk_filename, 'wb+')

        try:
            logger.info(f"Скачивается файл {smb_path}")
            _, _ = smb_connector.conn.retrieveFile(smb_connector.shared_folder, smb_path, file_obj)
            file_obj.seek(0)
            logger.info(f"Файл {disk_filename} сохранен на диск")
        finally:
            file_obj.close()

    return disk_filename


def process_data(json_data: dict):
    # закрывает открытые пдфки
    if json_data.get('file'):
        file_to_delete = None
        filename = json_data['file']

        for proc in psutil.process_iter(["name", "open_files"]):
            if proc.info.get("name") != "Acrobat.exe":
                continue
            try:
                for file in proc.info.get("open_files", []):
                    if file.path and '.pdf' in file.path:
                        logger.info(f"Закрывается файл {file.path}")
                        proc.kill()
                        file_to_delete = file.path
                        break
            except psutil.AccessDenied as e:
                logger.error(f"Ошибка доступа к процессу: {e}")
            except Exception as e:
                logger.error(f"Ошибка при закрытии PDF: {e}")

        if file_to_delete:
            try:
                logger.info(f"Файл {file_to_delete} удаляется с диска")
                os.remove(file_to_delete)
            except OSError as e:
                logger.error(f"Ошибка при удалении файла {file_to_delete} с диска: {e}")

        # открывает пдфку, скачивая ее с SMB
        new_file = _download_file_from_smb(filename=filename)
        logger.info(f'Открывается файл {new_file}')

        subprocess.Popen(
            # это откроет пдф-ку
            [
                config['EXE_PATH'],
                '/A',
                'page=1',
                new_file
            ],
            shell=False,
            stdout=subprocess.PIPE
        )


if __name__ == '__main__':
    logger.info(f"manual скрипт начал работу,"
                f" порт: {config['PORT']}, хост: {config['HOST']}",
          f"Папка с файлами: {config['FILES_DIR']}")
    try:
        start_server_socket(config['HOST'], int(config['PORT']), callback=process_data)
    except Exception as e:
        logger.error("Критическая ошибка скрипта")
