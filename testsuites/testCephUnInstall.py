from utils import zypperutils
from utils import cephdeploy
from utils import monitoring
from utils import operations
from utils import general
from utils import baseconfig
from nose.exc import SkipTest
from ConfigParser import SafeConfigParser
import logging,time,re, os, sys

log = logging.getLogger(__name__)

cfg_data = None
yaml_data = {}


def setup_module():
    global cfg_data
    global yaml_data
    filename = os.environ.get("CFG_FILE", "setup.cfg")

    cfg_data = SafeConfigParser()
    cfg_data.read(filename)

    yamlfile = os.environ.get("YAMLDATA_FILE")
    if yamlfile == None:
        yamlfile = __name__.split('.')[len(__name__.split('.'))-1]
        yamlfile = 'yamldata/%s.yaml' % (yamlfile)
    yaml_data = baseconfig.fetchTestYamlData(yamlfile)

    baseconfig.setLogger('cephauto.log', cfg_data)
    os.environ["CLIENTNODE"] = yaml_data['clientnode'][0]

    monitoring.printRPMVersions(cfg_data.get('env', 'repo_baseurl'))
    url = cfg_data.get('env', 'repo_baseurl')
    for node in yaml_data['allnodes']:
        zypperutils.addRepo('ceph', url, node)

    log.info('starting ceph clean up')
    general.perNodeCleanUp(yaml_data['allnodes'], 'ceph')


def tearDown():
    pass


def teardown_module():
    pass
