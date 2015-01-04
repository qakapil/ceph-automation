from utils import basetest
from utils import zypperutils
from utils import cephdeploy
from utils import monitoring
from utils import operations
from utils import general
import logging,time,re, os

log = logging.getLogger(__name__)

class TestInstallCheck(basetest.Basetest):

    @classmethod
    def setup_class(cls):
        filename = os.environ.get("CFG_FILE", "setup.cfg")
        cls.fetchIniData(cls, filename)
        cls.setLogger(cls,'cephauto.log')
        node = os.environ.get("CLIENTNODE")
        url = os.environ.get("ISO_URL")

        if zypperutils.isRepoPresent('ceph', node):
           zypperutils.removeRepo('ceph', node)
        if zypperutils.isRepoPresent('ceph-debug', node):
           zypperutils.removeRepo('ceph-debug', node)
        
        if os.environ.get("BASE_REPONAME"):
           base_reponame = os.environ.get("BASE_REPONAME")
        else:
           base_reponame = 'ibs-sle12'

        
        if os.environ.get("BASE_REPOURL"):
           base_url = os.environ.get("BASE_REPOURL")
        else:
           base_url = 'http://dist.suse.de/ibs/SUSE:/SLE-12:/GA/standard/'

        zypperutils.addRepo(base_reponame, base_url, node)
        
        if os.environ.get("ISO1"):
            sMedia1 = general.downloadISOAddRepo(url, 'Media1', 'ceph', node, os.environ.get("ISO1"))
        else:
            sMedia1 = general.downloadISOAddRepo(url, 'Media1', 'ceph', node)
       
        if os.environ.get("ISO2"):
            sMedia2 = general.downloadISOAddRepo(url, 'Media2', 'ceph-debug', node, os.environ.get("ISO2"))
        else:
            sMedia2 = general.downloadISOAddRepo(url, 'Media2', 'ceph-debug', node)
        
        cls.base_reponame = base_reponame
        cls.node = node
        cls.printData = {'iso_url':url, 'base_repo':base_url, 'iso_build':sMedia1}

    
    def setUp(self):
        log.info('++++++starting %s ++++++' % self._testMethodName)

   
    
    
    def testInstallCheck(self):
        try:
            general.runInstallCheck(self.node, self.base_reponame, 'ceph')
            general.runInstallCheck(self.node, self.base_reponame, 'ceph-debug')
        except  Exception as e:
            self.printData['InstallCheck_error'] = str(e)
            raise Exception(str(e))
    
    
    def tearDown(self):
        log.info('++++++completed %s ++++++' % self._testMethodName)
        
        
         
    @classmethod
    def teardown_class(self):
        log.info('++++++++++++++starting teardown_class+++++++++++++')
        f = open('jenkins_data.txt', 'w')
        for key, value in self.printData.iteritems():
            f.write(key+' = '+value+'\n\n')
        f.close()
        log.info('++++++++++++++Completed teardown_class++++++++++++')
