from utils import basetest
from utils import zypperutils
from utils import cephdeploy
from utils import general
import logging
#from nose import with_setup

log = logging.getLogger(__name__)

class TestSanity(basetest.Basetest):

    @classmethod
    def setup_class(cls):        
        cls.fetchIniData(cls)
        cls.fetchTestYamlData(cls,__name__)
        cls.setLogger(cls)
    
    def test0_createDirs(self):
        print('starting test0_createDirs')
        if not self.ctx.has_key('workingdir'):
            self.ctx['workingdir'] = '~/cephdeploy-cluster'
        general.createDir(self.ctx['workingdir'])
        for node in self.ctx['allnodes']:
            general.createDir('/var/lib/ceph/osd',node)
            general.createDir('/var/lib/ceph/bootstrap-osd',node)
        log.info('Completed test0_createDirs')
      
    def test1_AddRepo(self):
        log.info('starting test1_AddRepo')
        url = self.config.get('env','repo_baseurl')
        zypperutils.addRepo('ceph', url)
        log.info('Completed test1_AddRepo')
    
    def test2_InstallCephDeploy(self):
        log.info('starting the test test2_InstallCephDeploy')
        zypperutils.installPkg('ceph-deploy')
        log.info('Completed test2_InstallCephDeploy')
    
    def test3_DeclareInitialMons(self):
        log.info('starting test3_DeclareInitialMons')
        cephdeploy.decalreInitialMons(self.ctx['initmons'], self.ctx['workingdir'])
        log.info('Completed test3_DeclareInitialMons')
    
    def test4_installCeph(self):
        log.info('starting test4_installCeph')
        cephdeploy.installNodes(self.ctx['allnodes'], self.ctx['workingdir'])
        log.info('Completed test4_installCeph')
        
    def test5_createInitialMons(self):
        log.info('starting test5_createInitialMons')
        cephdeploy.createInitialMons(self.ctx['initmons'], self.ctx['workingdir'])
        log.info('Completed test5_createInitialMons')
    
    def test6_PrepareActivateOSDs(self):
        log.info('starting test6_PrepareActivateOSDs')
        cephdeploy.PrepareActivateOSDs(self.ctx['osds'], self.ctx['workingdir'])
        log.info('Completed test6_PrepareActivateOSDs')
    
    
    
    
if __name__ == "__main__":
    A = TestSanity()
    A.test3_DeclareInitialMons()
