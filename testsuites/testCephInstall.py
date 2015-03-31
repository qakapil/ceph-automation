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
    ceph_internal_url = cfg_data.get('env', 'ceph_internal_url')

    for node in yaml_data['allnodes']:
        zypperutils.addRepo('ceph', url, node)

    general.downloadISOAddRepo(ceph_internal_url, 'internal', 'ceph-internal',
                               os.environ["CLIENTNODE"], iso_name='SUSE-Enterprise-Storage-1.0-Internal-x86_64-GM-Media.iso')
    for pkg in ['rbd-kmp-default','qemu-block-rbd','qemu-tools']:
        zypperutils.installPkgFromRepo(pkg, os.environ["CLIENTNODE"], 'ceph-internal')

    before_cleanup = os.environ.get("BEFORE_CLEANUP")
    if before_cleanup is not None:
        log.info('starting teardown for before_cleanup')
        general.perNodeCleanUp(yaml_data['allnodes'], 'ceph')


def setUp():
    if os.environ.get("CLUSTER_FAILED") == "Yes":
       raise SkipTest("ceph cluster was not active+clean")
    log.info('++++++starting %s ++++++' % __name__)


def test02_InstallCephDeploy():
    zypperutils.installPkg('ceph-deploy', os.environ["CLIENTNODE"])


def test03_DeclareInitialMons():
    cephdeploy.declareInitialMons(yaml_data['initmons'])


def test04_InstallCeph():
    cephdeploy.installNodes(yaml_data['allnodes'])


def test05_CreateInitialMons():
    cephdeploy.createInitialMons(yaml_data['initmons'])


def test06_ZapOSDs():
    if yaml_data['osd_zap'] == None:
        log.info('No disks to zap. Skipping')
        return
    cephdeploy.osdZap(yaml_data['osd_zap'])


def test07_PrepareOSDs():
    cephdeploy.osdPrepare(yaml_data['osd_prepare'])


def test08_ActivateOSDs():
    cephdeploy.osdActivate(yaml_data['osd_activate'])


def test09_AdminNodes():
    cephdeploy.addAdminNodes(yaml_data['clientnode'])


def test10_ValidateCephStatus():
    time.sleep(10)
    fsid = monitoring.getFSID()
    status = monitoring.getCephStatus()
    if fsid not in status:
        raise Exception, "fsid %s was not found in ceph status %s"\
                         % (fsid, status)
    active_clean = False
    counter = 0
    default_pgs = monitoring.getTotalPGs()
    while not active_clean:
        if default_pgs +' active+clean' in status:
            log.info('placement groups in ceph status were \
                      active+clean')
            active_clean = True
            continue
        if (counter > 20):
            os.environ["CLUSTER_FAILED"] = "Yes"
            raise Exception, 'PGs did not reach active+clean state \
                               after 5 mins'
        log.debug('waiting for 5 seconds for ceph status to update')
        time.sleep(5)
        counter += 1
        status = monitoring.getCephStatus()
    if 'health HEALTH_WARN clock skew detected' in status:
        log.warning('health HEALTH_WARN clock skew detected in\
                     ceph status')
    if 'health HEALTH_OK' in status:
        log.warning('cluster health is OK and PGs are active+clean')


def test11_restartCeph():
    for node in yaml_data['initmons']:
        operations.restartCeph(node)


def test12_ValidateCephStatus():
    fsid = monitoring.getFSID()
    status = monitoring.getCephStatus()
    if fsid not in status:
        raise Exception, "fsid %s was not found in ceph status %s"\
                          % (fsid,status)
    active_clean = False
    counter = 0
    default_pgs = monitoring.getTotalPGs()
    while not active_clean:
        if default_pgs +' active+clean' in status:
            log.info('placement groups in ceph status were \
                      active+clean')
            active_clean = True
            continue
        if (counter > 20):
            raise Exception, 'PGs did not reach active+clean state \
                               after 5 mins'
        log.debug('waiting for 5 seconds for ceph status to update')
        time.sleep(5)
        counter += 1
        status = monitoring.getCephStatus()
    if 'health HEALTH_WARN clock skew detected' in status:
        log.warning('health HEALTH_WARN clock skew detected in\
                     ceph status')
    if 'health HEALTH_OK' in status:
        log.warning('cluster health is OK and PGs are active+clean')


def test13_ValidateCephDeployVersion():
    expVersion = cephdeploy.getExpectedVersion(
                            cfg_data.get('env','repo_baseurl'))
    actVersion = cephdeploy.getActuaVersion()
    if actVersion not in expVersion:
        raise Exception, "expected '%s' and actual '%s' versions \
                          did not match" % (expVersion,actVersion)


def test14_ValidateCephVersion():
    expVersion = monitoring.getExpectedVersion(
                 cfg_data.get('env','repo_baseurl'))
    actVersion = monitoring.getActuaVersion()
    if actVersion not in expVersion:
        raise Exception, "expected '%s' and actual '%s' \
            versions did not match" % (expVersion,actVersion)




def tearDown():
    log.info('++++++completed %s ++++++' % __name__)


def teardown_module():
    after_cleanup = os.environ.get("AFTER_CLEANUP")
    if after_cleanup == None:
        log.info('skipping teardown for after_cleanup')
        return
    log.info('++++++++++++++starting teardown_class+++++++++++++')
    cephdeploy.cleanupNodes(yaml_data['allnodes'],
                           'ceph')
    log.info('++++++++++++++Completed teardown_class++++++++++++')
