import datetime
import logging
from os import path, environ

LOG_LEVEL = logging.INFO

DORIS_EXPORT_FOLDER_PATH = environ.get('DORIS_EXPORT_FOLDER_PATH', '/data/doris')

FILE_METADATA_FOLDER_PATH = environ.get('FILE_METADATA_FOLDER_PATH', '/data/tmp/file_metadata')
FILE_MAPPING_FOLDER_PATH = environ.get('FILE_MAPPING_FOLDER_PATH', '/data/tmp/file_id2uuid_mapping')

TTL_FOLDER_PATH = environ.get('TTL_FOLDER_PATH', '/output/ttl')
LOG_FOLDER_PATH = environ.get('LOG_FOLDER_PATH', '/output/log')

NIEUWSBERICHTEN_DB_HOST = environ.get('NIEUWSBERICHTEN_DB_HOST', 'nieuwsberichten-db')


DORIS_EXPORT_URI = "http://doris.vlaanderen.be/export/" # With trailing slash!
NIEUWSBERICHTEN_EXPORT_URI = "http://nieuwsberichten.vonet.be/" # With trailing slash!

KALEIDOS_API_URI = "http://kanselarij.vo.data.gift/" # With trailing slash!
KALEIDOS_DOC_FILE_PATH = ""  # With trailing slash! relative to /share

GRAPH_NAME = 'http://mu.semte.ch/graphs/public'

KALEIDOS_SHARE_EXPORT_SUBFOLDER = '' # Subfolder within the share folder where the export files folder will be located

# PRIVATE
####################################################################################################

EXPORT_FILE_PATH_FS = "export dar_doris_{}_{}/metadata.csv"

DORIS_EXPORT_ENCODING = 'windows-1252'

BEGINDATUM_DORIS_REFERENTIES = datetime.date(1992, 12, 31)
BEGINDATUM_NIEUWSBERICHTEN = datetime.date(2006, 2, 10)

EXPORT_FILES = {
    'VR': {
        'document': path.join(DORIS_EXPORT_FOLDER_PATH, EXPORT_FILE_PATH_FS.format('vr', 'document')),
        'fiche': path.join(DORIS_EXPORT_FOLDER_PATH, EXPORT_FILE_PATH_FS.format('vr', 'fiche'))
    },
    'OC': {
        'document': path.join(DORIS_EXPORT_FOLDER_PATH, EXPORT_FILE_PATH_FS.format('oc', 'document')),
        'fiche': path.join(DORIS_EXPORT_FOLDER_PATH, EXPORT_FILE_PATH_FS.format('oc', 'fiche'))
    }
}

NIEUWSBERICHTEN_DB_CONFIG = {
    'host': NIEUWSBERICHTEN_DB_HOST,
    'user': 'root',
    'password': 'example',
    'db': 'NIEUWSBERICHTEN_P',
    'charset': 'utf8mb4',
}

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
fh = logging.FileHandler(path.join(LOG_FOLDER_PATH, 'kaleidos_conversion.log'))
logger.addHandler(fh)
sh = logging.StreamHandler()
logger.addHandler(sh)
