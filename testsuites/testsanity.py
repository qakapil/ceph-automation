from utils import basetest
from utils import zypperutils
from utils import cephdeploy
from utils import general
from utils import monitoring
import logging,time
#from nose import with_setup

log = logging.getLogger(__name__)

class TestSanity(basetest.Basetest):

    @classmethod
    def setup_class(cls):        
        cls.fetchIniData(cls)
        cls.fetchTestYamlData(cls,__name__)
        cls.setLogger(cls)
        monitoring.printRPMVersions(cls.config.get('env','repo_baseurl'))
        cephdeploy.cleanupNodes(cls.ctx['allnodes'], 
                                cls.config.get('env','repo_name'),
                                cls.ctx['workingdir'])
        
    def test00_createDirs(self):
        log.info('starting test0_createDirs')
        if not self.ctx.has_key('workingdir'):
            self.ctx['workingdir'] = '~/cephdeploy-cluster'
        general.createDir(self.ctx['workingdir'])
        for node in self.ctx['allnodes']:
            general.createDir('/var/lib/ceph/osd',node)
            general.createDir('/var/lib/ceph/bootstrap-osd',node)
        log.info('Completed test0_createDirs')
      
    def test01_AddRepo(self):
        log.info('starting test1_AddRepo')
        url = self.config.get('env','repo_baseurl')
        zypperutils.addRepo('ceph', url)
        log.info('Completed test1_AddRepo')
    
    def test02_InstallCephDeploy(self):
        log.info('starting the test test2_InstallCephDeploy')
        zypperutils.installPkg('ceph-deploy')
        log.info('Completed test2_InstallCephDeploy')
    
    def test03_DeclareInitialMons(self):
        log.info('starting test3_DeclareInitialMons')
        cephdeploy.decalreInitialMons(self.ctx['initmons'], 
                                      self.ctx['workingdir'])
        log.info('Completed test3_DeclareInitialMons')
    
    def test04_InstallCeph(self):
        log.info('starting test4_installCeph')
        cephdeploy.installNodes(self.ctx['allnodes'], 
                                self.ctx['workingdir'])
        log.info('Completed test4_installCeph')
        
    def test05_CreateInitialMons(self):
        log.info('starting test5_createInitialMons')
        cephdeploy.createInitialMons(self.ctx['initmons'], 
                                     self.ctx['workingdir'])
        log.info('Completed test5_createInitialMons')
    
    def test06_PrepareActivateOSDs(self):
        log.info('starting test6_PrepareActivateOSDs')
        cephdeploy.PrepareActivateOSDs(self.ctx['osds'], 
                                       self.ctx['workingdir'])
        log.info('Completed test6_PrepareActivateOSDs')
    
    def test07_AdminNodes(self):
        log.info('starting test7_AdminNodes')
        cephdeploy.addAdminNodes(self.ctx['allnodes'], 
                                 self.ctx['workingdir'])
        log.info('completed test7_AdminNodes')
    
    def test08_ValidateCephStatus(self):
        log.info('starting test8_ValidateCephStatus')
        fsid = monitoring.getFSID(self.ctx['workingdir'])
        status = monitoring.getCephStatus()
        if fsid not in status:
            raise Exception, "fsid %s was not found in ceph status %s" \
                              % (fsid,status)
        active_clean = False
        counter = 0
        while not active_clean:
            if '192 active+clean' in status:
                log.info('placement groups in ceph status were \
                          active+clean')
                active_clean = True
                continue
            if (counter > 300):
                raise Exception, 'PGs did not reach active+clean state \
                                   after 5 mins'
            log.debug('waiting for 5 seconds for ceph status to update')
            time.sleep()
            counter += 1
            status = monitoring.getCephStatus()
        if 'health HEALTH_WARN clock skew detected' in status:
            log.warning('health HEALTH_WARN clock skew detected in\
                         ceph status')
        if 'health HEALTH_OK' in status:
            log.warning('cluster health is OK and PGs are active+clean') 
        log.info('completed test8_ValidateCephStatus')
    
    def test09_ValidateCephDeployVersion(self):
        log.info('starting test9_ValidateCephVersion')
        expVersion = cephdeploy.getExpectedVersion(self.config.get('env','repo_baseurl'))
        actVersion = cephdeploy.getActuaVersion()
        if actVersion not in expVersion:
            raise Exception, "expected '%s' and actual '%s' versions did not match" % (expVersion,actVersion)
        log.info('completed test9_ValidateCephVersion')
     
    def test10_ValidateCephVersion(self):
        log.info('starting test10_ValidateCephVersion')
        expVersion = monitoring.getExpectedVersion(self.config.get('env','repo_baseurl'))
        actVersion = monitoring.getActuaVersion()
        if actVersion not in expVersion:
            raise Exception, "expected '%s' and actual '%s' versions did not match" % (expVersion,actVersion)
        log.info('completed test10_ValidateCephVersion')
     
     
    @classmethod
    def teardown_class(self):
        log.info('starting teardown_class')
        cephdeploy.cleanupNodes(self.ctx['allnodes'], 
                                self.config.get('env','repo_name'), 
                                self.ctx['workingdir'])
        log.info('Completed teardown_class')