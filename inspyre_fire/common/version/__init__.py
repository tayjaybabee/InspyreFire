from inspyre_toolbox.ver_man.classes import VersionParser, PyPiVersionInfo
from inspyre_toolbox.ver_man.helpers import get_version_string_from_file, provision_path
from inspyre_fire.common import PACKAGE_NAME


THIS_FILES_DIR = provision_path(__file__).parent
VERSION_FILE_PATH = THIS_FILES_DIR / 'VERSION'

__VERSION_STR__ = get_version_string_from_file(VERSION_FILE_PATH)
VERSION = VersionParser(__VERSION_STR__)
PYPI_VERSION_INFO = PyPiVersionInfo(package_name=PACKAGE_NAME)
