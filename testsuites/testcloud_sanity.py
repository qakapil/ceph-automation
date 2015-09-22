from utils import basetest
from utils import monitoring
from utils import operations
from utils import rbd_operations
import logging,time,re, os
#from nose import with_setup

log = logging.getLogger(__name__)

class TestSanity(basetest.Basetest):

    @classmethod
    def setup_class(cls):
        filename = os.environ.get("CFG_FILE", "setup.cfg")
        cls.fetchIniData(cls, filename)
        yamlfile = os.environ.get("YAMLDATA_FILE")
        if yamlfile == None:
            yamlfile = __name__.split('.')[len(__name__.split('.'))-1]
            yamlfile = 'yamldata/%s.yaml' % (yamlfile)
        cls.fetchTestYamlData(cls,yamlfile)
        cls.setLogger(cls, 'cephauto.log')
        os.environ["CLIENTNODE"] = cls.ctx['clientnode']

    def setUp(self):
        log.info('++++++starting %s ++++++' % self._testMethodName)

    def test01_ValidateCephStatus(self):
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

    def test02_ValidateCephHealth(self):
        fsid = monitoring.getFSID()
        status = monitoring.getCephStatus()
        if fsid not in status:
            raise Exception, "fsid %s was not found in ceph status %s"\
                              % (fsid,status)
        health_ok = False
        counter = 0
        while not health_ok:
            if (counter > 20):
                raise Exception, 'cluster health was no OK'
            log.debug('waiting for 5 seconds for ceph status to update')
            time.sleep(120)
            counter += 1
            status = monitoring.getCephStatus()
            if 'health HEALTH_WARN clock skew detected' in status:
                log.warning('health HEALTH_WARN clock skew detected in\
                             ceph status')
            if 'health HEALTH_OK' in status:
                health_ok = True
                log.warning('cluster health is OK and PGs are active+clean')
            else:
                pass
                #for node in self.ctx['initmons']:
                    #operations.restartCeph(node)

    def test03_ValidateCephVersion(self):
        expVersion = self.ctx['ceph_version']
        actVersion = monitoring.getActuaVersion()
        if expVersion not in actVersion:
            raise Exception, "expected '%s' and actual '%s' \
                versions did not match" % (expVersion,actVersion)

    def test04_ValidateDefaultPools(self):
        def_pools = monitoring.getDefaultPools()
        assert ('0 rbd,' in def_pools),"The default \
        pools were %s" % def_pools

    def test05_CreatePools(self):
        for pool in self.ctx['createpools']:
            operations.createPool(pool)

    def test06_ValidatePools(self):
        for pool in self.ctx['createpools']:
            operations.validatePool(pool)

    def test07_CreateImages(self):
        for image in self.ctx['images']:
            rbd_operations.createRBDImage(image)

    def test08_RemoveImages(self):
        for image in self.ctx['images']:
            rbd_operations.rbdRemovePoolImage(image)

    def test09_ValidateMonStat(self):
        mon_stat = monitoring.getMonStat()
        log.info("the mon stat is "+ str(mon_stat))
        matchObj = re.match( r'.*:(.*) mons at .* quorum (.*?) (.*)', mon_stat, re.M|re.I)
        assert(len(self.ctx['initmons']) == int(matchObj.group(1))),\
        "the number of mons active were not as expected"
        assert(len(self.ctx['initmons']) == len(matchObj.group(2).split(','))),\
        "the number of mons in quorum were not as expected"
        assert(sorted(self.ctx['initmons']) == sorted(matchObj.group(3).split(','))),\
        "the monlist in quorum was not as expected"

    def test10_ValidateOSDStat(self):
        osd_stat = monitoring.getOSDStat()
        n = len(self.ctx['osds'])
        expStr = "%s osds: %s up, %s in" % (n,n,n)
        assert(expStr in osd_stat),"osd stat validation failed"

    def test11_RadosObjects(self):
        for radosobject in self.ctx['radosobjects']:
            operations.createValidateObject(radosobject)
        for radosobject in self.ctx['radosobjects']:
            operations.removeObject(radosobject)

    def test12_DeletePools(self):
        for pool in self.ctx['createpools']:
            operations.deletePool(pool)

    def test13_Validatelibrbd(self):
        operations.validateLibRbdTests()

    def test14_ValidateDefaultOSDtree(self):
        str_osd_tree = monitoring.getOSDtree()
        osd_tree = str_osd_tree.split('\n')
        for i in range(len(osd_tree)-1):
            osd_tree[i] = osd_tree[i].split()
        indx = osd_tree[0].index('WEIGHT')
        for i in range(len(osd_tree)-1):
            value = osd_tree[i][indx].strip()
            assert('0' != value),"the weight of the\
            osd was zero \n"+str_osd_tree

    def test15_restartRadosGW(self):
        operations.restartRadosGW(self.ctx['radosgw_node'])

    def tearDown(self):
        log.info('++++++completed %s ++++++' % self._testMethodName)
