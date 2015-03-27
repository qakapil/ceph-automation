from utils import zypperutils
from utils import cephdeploy
from utils import monitoring
from utils import operations
from utils import general
from utils import rgw_tasks
from utils import baseconfig
from nose.exc import SkipTest
import logging,time,re, os, sys

log = logging.getLogger(__name__)

cfg_data = {}
yaml_data = {}


def setup_module():
    global cfg_data
    global yaml_data
    filename = os.environ.get("CFG_FILE", "setup.cfg")
    cfg_data = baseconfig.fetchIniData(filename)

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

    before_cleanup = os.environ.get("BEFORE_CLEANUP")
    if before_cleanup is not None:
        log.info('starting teardown for before_cleanup')
        general.perNodeCleanUp(yaml_data['allnodes'], 'ceph')


def setUp():
    if os.environ.get("CLUSTER_FAILED") == "Yes":
       raise SkipTest("ceph cluster was not active+clean")
    log.info('++++++starting %s ++++++' % self._testMethodName)


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
                            self.config.get('env','repo_baseurl'))
    actVersion = cephdeploy.getActuaVersion()
    if actVersion not in expVersion:
        raise Exception, "expected '%s' and actual '%s' versions \
                          did not match" % (expVersion,actVersion)


def test14_ValidateCephVersion():
    expVersion = monitoring.getExpectedVersion(
                 self.config.get('env','repo_baseurl'))
    actVersion = monitoring.getActuaVersion()
    if actVersion not in expVersion:
        raise Exception, "expected '%s' and actual '%s' \
            versions did not match" % (expVersion,actVersion)


def test15_ValidateDefaultPools():
    def_pools = monitoring.getDefaultPools()
    assert ('0 data,1 metadata,2 rbd,' in def_pools),"The default \
    pools were %s" % def_pools


def test16_CreateImages():
    for image in yaml_data['images']:
        operations.createRBDImage(image)


def test17_RemoveImages():
    for image in yaml_data['images']:
        operations.rbdRemovePoolImage(image)


def test18_ValidateMonStat():
    mon_stat = monitoring.getMonStat()
    log.info("the mon stat is "+ str(mon_stat))
    matchObj = re.match( r'.*:(.*) mons at .* quorum (.*?) (.*)', mon_stat, re.M|re.I)
    assert(len(yaml_data['initmons']) == int(matchObj.group(1))),\
    "the number of mons active were not as expected"
    assert(len(yaml_data['initmons']) == len(matchObj.group(2).split(','))),\
    "the number of mons in quorum were not as expected"
    assert(sorted(yaml_data['initmons']) == sorted(matchObj.group(3).split(','))),\
    "the monlist in quorum was not as expected"


def test19_ValidateOSDStat():
    osd_stat = monitoring.getOSDStat()
    n = len(yaml_data['osd_activate'])
    expStr = "%s osds: %s up, %s in" % (n,n,n)
    assert(expStr in osd_stat),"osd stat validation failed"


def test20_RadosObjects():
    for radosobject in yaml_data['radosobjects']:
        operations.createValidateObject(radosobject)
    for radosobject in yaml_data['radosobjects']:
        operations.removeObject(radosobject)


def test21_CreatePools():
    for pool in yaml_data['createpools']:
        operations.createPool(pool)


def test22_ValidatePools():
    for pool in yaml_data['createpools']:
        operations.validatePool(pool)


def test23_DeletePools():
    for pool in yaml_data['createpools']:
        operations.deletePool(pool)


def test24_Validatelibrbd():
    operations.validateLibRbdTests()


def test25_ValidateDefaultOSDtree():
    str_osd_tree = monitoring.getOSDtree()
    osd_tree = str_osd_tree.split('\n')
    for i in range(len(osd_tree)-1):
        osd_tree[i] = osd_tree[i].split('\t')
    indx = osd_tree[0].index('weight')
    for i in range(len(osd_tree)-1):
        value = osd_tree[i][indx].strip()
        assert('0' != value),"the weight of the\
        osd was zero \n"+str_osd_tree


def test26_InvalidDiskOSDPrepare():
    rc = cephdeploy.prepareInvalidOSD(yaml_data['osd_activate'])
    assert (rc == 1), "OSD Prepare for invalid disk did not fail"


def test27_CreateRGW():
    for rgw in yaml_data['rgws']:
        rgw_tasks.create_rgw(rgw['rgw-host'], rgw['rgw-name'])
    for rgw in yaml_data['rgws']:
        rgw_tasks.verifyRGWList(rgw['rgw-host'], rgw['rgw-name'])


def test28_restartRadosGW():
    for rgw in yaml_data['rgws']:
        operations.restartRadosGW(rgw['rgw-host'])


def test29_S3Tests():
    rgw_tasks.prepareS3Conf(yaml_data['rgws'][0])
    rgw_tasks.createS3TestsUsers(yaml_data['rgws'][0]['rgw-host'],
                          yaml_data['rgws'][0]['rgw-name'])
    rgw_tasks.executeS3Tests()


def test30_SwiftTests():
    rgw_tasks.prepareSwiftConf(yaml_data['rgws'][0])
    rgw_tasks.createSwiftTestsUsers(yaml_data['rgws'][0]['rgw-host'],
                          yaml_data['rgws'][0]['rgw-name'])
    rgw_tasks.executeSwiftTests()


def tearDown():
    log.info('++++++completed %s ++++++' % self._testMethodName)


def teardown_module():
    after_cleanup = os.environ.get("AFTER_CLEANUP")
    if after_cleanup == None:
        log.info('skipping teardown for after_cleanup')
        return
    log.info('++++++++++++++starting teardown_class+++++++++++++')
    cephdeploy.cleanupNodes(yaml_data['allnodes'],
                           'ceph')
    log.info('++++++++++++++Completed teardown_class++++++++++++')
