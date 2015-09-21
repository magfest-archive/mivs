from urllib.request import urlopen

from sqlalchemy.types import LargeBinary

from uber.common import *
from mivs._version import __version__
from mivs.config import *
from mivs.models import *
import mivs.model_checks
import mivs.automated_emails

static_overrides(join(mivs_config['module_root'], 'static'))
template_overrides(join(mivs_config['module_root'], 'templates'))
mount_site_sections(mivs_config['module_root'])
