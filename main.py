import time

import psutil
import subprocess
import os

from dotenv import dotenv_values, load_dotenv
from holz_smb_connector import SMBConnector
from logger import logger
from server_socket import start_server_socket

load_dotenv('.env')
config = dotenv_values(".env")


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
        except Exception as e:
            logger.error('Ошибка при скачивании файла с smb')
            return None
        finally:
            file_obj.close()

    return disk_filename


def process_data(json_data: dict):
    # закрывает открытые файлы
    logger.info("1")

    if json_data.get('file'):
        files_to_delete = []
        filename = json_data['file']
        logger.info("2")

        for proc in psutil.process_iter(["name", "open_files"]):
            if proc.info.get("name") == "msedge.exe":
                try:
                    for file in proc.info.get("open_files", []):
                        if file.path and (file.path.endswith('.pdf') or file.path.endswith('.svg')):
                            logger.info(f"Закрывается файл {file.path}")
                            files_to_delete.append(file.path)
                    proc.kill()
                except psutil.AccessDenied as e:
                    logger.error(f"Ошибка доступа к процессу: {e}")
                except Exception as e:
                    logger.error(f"Ошибка при закрытии файла: {e}")
        logger.info("3")

        if files_to_delete:
            for file_to_delete in files_to_delete:
                try:
                    logger.info(f"Файл {file_to_delete} удаляется с диска")
                    os.remove(file_to_delete)
                except OSError as e:
                    logger.error(f"Ошибка при удалении файла {file_to_delete} с диска: {e}")
        logger.info("4")

        # открывает пдфку, скачивая ее с SMB
        new_file = _download_file_from_smb(filename=filename)
        logger.info("5")

        if new_file:
            try:
                logger.info(f'Открывается файл {new_file}')
                subprocess.Popen(
                    # это откроет пдф-ку
                    [
                        config['EXE_PATH'],
                        '/A',
                        '--InPrivate',
                        new_file
                    ],
                    shell=False,
                    stdout=subprocess.PIPE
                )
                logger.info(f'Файл {new_file} открыт')
            except Exception as e:
                logger.error(f'Проблема с открытием файла: {new_file}')
        time.sleep(3)


if __name__ == '__main__':
    logger.info(f"""
        Manual скрипт начал работу.
        Хост: {config['HOST']}.
        Порт: {config['PORT']}.
        SMB: {config['SMB_HOST']}, {config['SMB_WORK_DIR']}.
        Папка с файлами: {config['FILES_DIR']}.
        """
    )
    try:
        start_server_socket(config['HOST'], int(config['PORT']), callback=process_data)
    except Exception as e:
        logger.error("Критическая ошибка скрипта")
