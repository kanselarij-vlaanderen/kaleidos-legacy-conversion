import datetime
import logging
from os import path, environ

LOG_LEVEL = logging.getLevelName(environ.get('LOG_LEVEL', 'INFO'))

DORIS_EXPORT_FOLDER_PATH = '/data/doris'
DORIS_EXPORT_SUBFOLDER_FS = '{0}/dar_doris_{1}_{2}/'
DORIS_EXPORT_METADATA_FN = "metadata_enc_fixes.csv"
DORIS_EXPORT_METADATA_ENCODING = 'utf-8'
DORIS_EXPORT_FILE_SUBFOLDER = 'content'

FILE_METADATA_FOLDER_PATH = environ.get('FILE_METADATA_FOLDER_PATH', '/data/tmp/file_metadata')

TTL_FOLDER_PATH = environ.get('TTL_FOLDER_PATH', '/output/ttl')
LOG_FOLDER_PATH = environ.get('LOG_FOLDER_PATH', '/output/log')

NIEUWSBERICHTEN_DB_HOST = environ.get('NIEUWSBERICHTEN_DB_HOST', 'nieuwsberichten-db')


DORIS_EXPORT_URI = "http://doris.vlaanderen.be/export/" # With trailing slash!
NIEUWSBERICHTEN_EXPORT_URI = "http://nieuwsberichten.vonet.be/node/" # With trailing slash!

KALEIDOS_API_URI = "http://kanselarij.vo.data.gift/" # With trailing slash!
KALEIDOS_DOC_FILE_PATH = ""  # With trailing slash! relative to /share

GRAPH_NAME = 'http://mu.semte.ch/graphs/public'

# location within the app's share folder that will contain the contents of DORIS_EXPORT_FOLDER_PATH
KALEIDOS_SHARE_EXPORT_SUBFOLDER = environ.get('KALEIDOS_SHARE_EXPORT_SUBFOLDER', 'doris_exports')


FILE_MAPPING_FOLDER_PATH = environ.get('FILE_MAPPING_FOLDER_PATH', '/data/tmp/file_id2uuid_mapping')

THEME_MAPPING_FILE_PATH = "/data/tmp/theme_id2uuid_mapping.json"

SUBMITTER_MAPPING_FILE_PATH = "/data/tmp/submitter_ref2uuid_mapping.json"

# PRIVATE
####################################################################################################

BEGINDATUM_DORIS_REFERENTIES = datetime.date(1992, 12, 31)
BEGINDATUM_NIEUWSBERICHTEN = datetime.date(2006, 2, 10)

DORIS_EXPORT_METADATA_PATH_FS = path.join(DORIS_EXPORT_FOLDER_PATH,
                                          DORIS_EXPORT_SUBFOLDER_FS,
                                          DORIS_EXPORT_METADATA_FN)
EXPORT_FILES = {
    'VR': {
        'document': DORIS_EXPORT_METADATA_PATH_FS.format('VR', 'vr', 'document'),
        'fiche': DORIS_EXPORT_METADATA_PATH_FS.format('VR', 'vr', 'fiche'),
    },
    'OC': {
        'document': DORIS_EXPORT_METADATA_PATH_FS.format('OC', 'oc', 'document'),
        'fiche': DORIS_EXPORT_METADATA_PATH_FS.format('OC', 'oc', 'fiche'),
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
