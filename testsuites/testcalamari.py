from utils import basetest
from utils import zypperutils
from utils import calamari_tasks
import logging, os
#from nose import with_setup

log = logging.getLogger(__name__)

class TestSanity(basetest.Basetest):

    @classmethod
    def setup_class(cls):
        filename = os.environ.get("CFG_FILE", "setup.cfg")    
        cls.fetchIniData(cls, filename)
        yamlfile = os.environ.get("CALAMARI_YAMLDATA_FILE")
        if yamlfile == None:
            yamlfile = __name__.split('.')[len(__name__.split('.'))-1]
            yamlfile = 'yamldata/%s.yaml' % (yamlfile)
        cls.yamlfile = yamlfile
        cls.fetchTestYamlData(cls,yamlfile)
        cls.setLogger(cls,'calamariauto.log')
        os.environ["CALAMARI_NODE"] = cls.ctx['master_fqdn'].split('.')[0]
        before_cleanup = os.environ.get("BEFORE_CLEANUP")
        if before_cleanup != None:
            log.info('starting teardown for before_cleanup')
            calamari_tasks.cleanupStaleNodes(cls.ctx['allnodes'])
            calamari_tasks.cleanupCalamari()
    
    def setUp(self):
        log.info('++++++starting %s ++++++' % self._testMethodName)

   
    
    def test01_InstallCalamariServerTests(self):
        url = self.config.get('env','repo_baseurl')
        #url = 'http://'+self.ctx['clientnode_ip']+'/SLE12'
        zypperutils.addRepo('ceph', url, os.environ["CALAMARI_NODE"])
        zypperutils.installPkg('calamari-server-test', os.environ["CALAMARI_NODE"])
    
    
        
    def test02_InitializeCalamari(self):
        calamari_tasks.initializeCalamari()
    
    
    
    def test03_AllUnitTests(self):
        calamari_tasks.runUnitTests()
        
    
    '''
    def test04_AllAPITests(self):
        calamari_tasks.runRestAPITests()
    '''
    
    
    def test05_ServerTests(self):
        log.info(self.yamlfile)
        calamari_tasks.copyClusterConf(self.yamlfile)
        calamari_tasks.runServerTests()
        
        
        
    def tearDown(self):
        log.info('++++++completed %s ++++++' % self._testMethodName)
        
        
         
    @classmethod
    def teardown_class(self):
        after_cleanup = os.environ.get("AFTER_CLEANUP")
        if after_cleanup == None:
            log.info('skipping teardown for after_cleanup')
            return
        log.info('++++++++++++++starting teardown_class+++++++++++++')
        calamari_tasks.cleanupCalamari()
        log.info('++++++++++++++Completed teardown_class++++++++++++')
