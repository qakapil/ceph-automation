from utils import basetest
from utils import zypperutils
from utils import cephdeploy
from utils import monitoring
from utils import operations
from utils import general
from utils import rbd_operations
from utils import rgw_tasks
import logging,time,re, os, sys
from nose.plugins.skip import SkipTest

#from nose.exc import SkipTest
#from nose.tools import nottest

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
        cls.setLogger(cls,'cephauto.log')
        os.environ["CLIENTNODE"] = cls.ctx['clientnode'][0]
        monitoring.printRPMVersions(cls.config.get('env','repo_baseurl'))

        general.removeOldRepos(cls.ctx['allnodes'], ['ceph-debug','ceph_extras'])

        url = cls.config.get('env','repo_baseurl')
        for node in cls.ctx['allnodes']:
            zypperutils.addRepo('ceph', url, node)


        before_cleanup = os.environ.get("BEFORE_CLEANUP")
        if before_cleanup != None:
            log.info('starting teardown for before_cleanup')
            #cephdeploy.cleanupNodes(cls.ctx['allnodes'], 'ceph')
            general.perNodeCleanUp(cls.ctx['allnodes'], 'ceph')

    
    def setUp(self):
        if os.environ.get("CLUSTER_FAILED") == "Yes":
           raise SkipTest("ceph cluster was not active+clean") 
        log.info('++++++starting %s ++++++' % self._testMethodName)

    
    def test01_InstallCephDeploy(self):
        zypperutils.installPkg('ceph-deploy', os.environ["CLIENTNODE"])
    
    
    def test02_DeclareInitialMons(self):
        cephdeploy.declareInitialMons(self.ctx['initmons'])
    
    
    
    def test03_InstallCeph(self):
        cephdeploy.installNodes(self.ctx['allnodes']) 
    
    
    def test04_CreateInitialMons(self):
        cephdeploy.createInitialMons(self.ctx['initmons'])
    
    
    
    def test05_ZapOSDs(self):
        if self.ctx['osd_zap'] == None:
            log.info('No disks to zap. Skipping')
            return
        cephdeploy.osdZap(self.ctx['osd_zap'])
    
    
    def test06_PrepareOSDs(self):
        cephdeploy.osdPrepare(self.ctx['osd_prepare'])
    
    def test07_ActivateOSDs(self):
        cephdeploy.osdActivate(self.ctx['osd_activate'])
    
    
    def test08_AdminNodes(self):
        cephdeploy.addAdminNodes(self.ctx['clientnode'])
    
    
               
    def test09_ValidateCephStatus(self):
        time.sleep(10)
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
    

    def test10_restartCeph(self):
        for node in self.ctx['initmons']:
            operations.restartCeph(node)
    

    def test11_ValidateCephHealth(self):
        fsid = monitoring.getFSID()
        status = monitoring.getCephStatus()
        if fsid not in status:
            raise Exception, "fsid %s was not found in ceph status %s"\
                              % (fsid,status)
        health_ok = False
        counter = 0
        while not health_ok:
            if (counter > 40):
                raise Exception, 'cluster health was no OK'
            log.debug('waiting for 5 seconds for ceph status to update')
            time.sleep(10)
            counter += 1
            status = monitoring.getCephStatus()
            if 'health HEALTH_WARN clock skew detected' in status:
                log.warning('health HEALTH_WARN clock skew detected in\
                             ceph status')
            if 'health HEALTH_OK' in status:
                health_ok = True
                log.warning('cluster health is OK and PGs are active+clean')
            else:
                for node in self.ctx['initmons']:
                    operations.restartCeph(node)


    
    def test12_ValidateCephDeployVersion(self):
        expVersion = cephdeploy.getExpectedVersion(
                                self.config.get('env','repo_baseurl'))
        actVersion = cephdeploy.getActuaVersion()
        if (actVersion not in expVersion):
            raise Exception, "expected '%s' and actual '%s' versions \
                              did not match" % (expVersion,actVersion)
     

    def test13_ValidateCephVersion(self):
        expVersion = monitoring.getExpectedVersion(
                     self.config.get('env','repo_baseurl'))
        actVersion = monitoring.getActuaVersion()
        #if actVersion not in expVersion:
            #raise Exception, "expected '%s' and actual '%s' \
                #versions did not match" % (expVersion,actVersion)
        if '0.94-'not in actVersion:
            raise Exception, "actual version of ceph '%s' did not include '0.94.' " % actVersion
        if '0.94.'not in expVersion:
            raise Exception, "expected version of ceph '%s' did not include '0.94' " % expVersion
    
    def test14_ValidateDefaultPools(self):
        def_pools = monitoring.getDefaultPools()
        assert ('0 rbd,' in def_pools),"The default \
        pools were %s" % def_pools
    
    def test15_CreatePools(self):
        for pool in self.ctx['createpools']:
            operations.createPool(pool)

    def test16_ValidatePools(self):
        for pool in self.ctx['createpools']:
            operations.validatePool(pool)

 
    def test17_CreateImages(self):
        for image in self.ctx['images']:
            rbd_operations.createRBDImage(image)
    
    def test18_RemoveImages(self):
        for image in self.ctx['images']:
            rbd_operations.rbdRemovePoolImage(image)

    def test19_ValidateMonStat(self):
        mon_stat = monitoring.getMonStat()
        log.info("the mon stat is "+ str(mon_stat))
        matchObj = re.match( r'.*:(.*) mons at .* quorum (.*?) (.*)', mon_stat, re.M|re.I)
        assert(len(self.ctx['initmons']) == int(matchObj.group(1))),\
        "the number of mons active were not as expected"
        assert(len(self.ctx['initmons']) == len(matchObj.group(2).split(','))),\
        "the number of mons in quorum were not as expected"
        assert(sorted(self.ctx['initmons']) == sorted(matchObj.group(3).split(','))),\
        "the monlist in quorum was not as expected"

    
    def test20_ValidateOSDStat(self):
        osd_stat = monitoring.getOSDStat()
        n = len(self.ctx['osd_activate'])
        expStr = "%s osds: %s up, %s in" % (n,n,n)
        assert(expStr in osd_stat),"osd stat validation failed" 
    
    def test21_RadosObjects(self):
        for radosobject in self.ctx['radosobjects']:
            operations.createValidateObject(radosobject)
        for radosobject in self.ctx['radosobjects']:
            operations.removeObject(radosobject)
    
    
       
    def test22_DeletePools(self):
        for pool in self.ctx['createpools']:
            operations.deletePool(pool)
    
    def test23_Validatelibrbd(self):
        operations.validateLibRbdTests()
        
    
    def test25_ValidateDefaultOSDtree(self):
        str_osd_tree = monitoring.getOSDtree()
        osd_tree = str_osd_tree.split('\n')
        for i in range(len(osd_tree)-1):
            osd_tree[i] = osd_tree[i].split()
        indx = osd_tree[0].index('WEIGHT')
        for i in range(len(osd_tree)-1):
            value = osd_tree[i][indx].strip()
            assert('0' != value),"the weight of the\
            osd was zero \n"+str_osd_tree

    
    def test25_InvalidDiskOSDPrepare(self): 
        rc = cephdeploy.prepareInvalidOSD(self.ctx['osd_activate'])
        assert (rc == 1), "OSD Prepare for invalid disk did not fail"
    
    def test26_CreateRGW(self):
        for rgw in self.ctx['rgws']:
            apache = rgw.get('apache', None)
            log.info('APACHE '+str(apache))
            rgw_tasks.create_rgw(rgw['rgw-host'], rgw['rgw-name'], rgw['rgw-port'], apache=apache)
        for rgw in self.ctx['rgws']:
            rgw_tasks.verifyRGWList(rgw['rgw-host'], rgw['rgw-name'])

    def test27_restartRadosGW(self):
        for rgw in self.ctx['rgws']:
            operations.restartRadosGW(rgw['rgw-host'])


    def test28_S3Tests(self):
        rgw_tasks.prepareS3Conf(self.ctx['rgws'][0])
        rgw_tasks.createS3TestsUsers(self.ctx['rgws'][0]['rgw-host'],
                              self.ctx['rgws'][0]['rgw-name'])
        rgw_tasks.executeS3Tests()

    def test29_SwiftTests(self):
        rgw_tasks.prepareSwiftConf(self.ctx['rgws'][0])
        rgw_tasks.createSwiftTestsUsers(self.ctx['rgws'][0]['rgw-host'],
                              self.ctx['rgws'][0]['rgw-name'])
        rgw_tasks.executeSwiftTests()


    def test31_ValidateLogrotate(self):
        if general.doesFileExist('/usr/sbin/logrotate', os.environ["CLIENTNODE"]) != True:
            assert(False), '/usr/sbin/logrotate was not present'
        if  general.doesRegularFileExist('/etc/logrotate.d/ceph', os.environ["CLIENTNODE"]) != True:
            assert(False), '/etc/logrotate.d/ceph was not present'
        cmd = 'ssh %s sudo /usr/sbin/logrotate -f /etc/logrotate.d/ceph' % os.environ["CLIENTNODE"]
        if general.doesCommandPass(cmd) != True:
            assert(False), 'command /usr/sbin/logrotate -f /etc/logrotate.d/ceph failed'

    def test32_Validate50rbdrules(self):
        if  general.doesRegularFileExist('/usr/lib/udev/rules.d/50-rbd.rules', os.environ["CLIENTNODE"]) != True:
            assert(False), '/usr/lib/udev/rules.d/50-rbd.rules'
        srcpkg = general.getFileSource('/usr/lib/udev/rules.d/50-rbd.rules', os.environ["CLIENTNODE"])
        if 'ceph-common' not in srcpkg:
            assert(False), 'ceph-common was not the source package'


    def tearDown(self):
        log.info('++++++completed %s ++++++' % self._testMethodName)
        
        
         
    @classmethod
    def teardown_class(self):
        after_cleanup = os.environ.get("AFTER_CLEANUP")
        if after_cleanup == None:
            log.info('skipping teardown for after_cleanup')
            return
        log.info('++++++++++++++starting teardown_class+++++++++++++')
        cephdeploy.cleanupNodes(self.ctx['allnodes'], 
                               'ceph')
        log.info('++++++++++++++Completed teardown_class++++++++++++')
