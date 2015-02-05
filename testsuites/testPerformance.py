from utils import basetest
from utils import zypperutils
from utils import cephdeploy
from utils import monitoring
from utils import operations
from utils import general
from threading import Thread
import logging,time,re, os, threading
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
        cls.setLogger(cls,'cephauto.log')
        os.environ["CLIENTNODE"] = cls.ctx['clientnode'][0]
        #monitoring.printRPMVersions(cls.config.get('env','repo_baseurl'))
        
        cls.ctx['iso_build_num'] = general.getISOBuildNum(\
                                   cls.config.get('env','iso_url_stable'))
    
        before_cleanup = os.environ.get("BEFORE_CLEANUP")
        if before_cleanup != None:
            log.info('starting teardown for before_cleanup')
            cephdeploy.cleanupNodes(cls.ctx['allnodes'], 
                                    'ceph')
            general.removeOldxcdFiles()
            
    
    def setUp(self):
        if os.environ.get("CLUSTER_FAILED") == "Yes":
           raise SkipTest("ceph cluster was not active+clean")
        log.info('++++++starting %s ++++++' % self._testMethodName)

   
    
    def test00_AddISORepo(self):
        general.installStartLighthttp(os.environ["CLIENTNODE"])
        general.mountISO(self.ctx['iso_build_num'], staging=False)
        url = 'http://'+self.ctx['clientnode_ip']+'/SLE12'
        for node in self.ctx['allnodes']:
            zypperutils.addRepo('ceph', url, node)
    
    def test01_xcdchk(self):
        general.runXCDCHK(self.ctx['iso_build_num'])
    
    
    def test02_InstallCephDeploy(self):
        zypperutils.installPkg('ceph-deploy', os.environ["CLIENTNODE"])
    
    
    def test03_DeclareInitialMons(self):
        cephdeploy.declareInitialMons(self.ctx['initmons'])
        general.updateCephConf_NW(self.ctx['public_nw'], self.ctx['cluster_nw'])
    
    
    def test04_InstallCeph_ISO(self):
        cephdeploy.installNodes(self.ctx['allnodes'])
        
    
    
    def test05_CreateInitialMons(self):
        cephdeploy.createInitialMons(self.ctx['initmons'])
    
    
    
    def test06_ZapOSDs(self):
        if self.ctx['osd_zap'] == None:
            log.info('No disks to zap. Skipping')
            return
        cephdeploy.osdZap(self.ctx['osd_zap'])
    
    
    def test07_PrepareOSDs(self):
        cephdeploy.osdPrepare(self.ctx['osd_prepare'])
    
    
    
    def test09_AdminNodes(self):
        cephdeploy.addAdminNodes(self.ctx['clientnode'])
        for node in self.ctx['clientnode']:
            general.installPkgFromurl(node, 
            "http://download.suse.de/ibs/Devel:/Storage:/1.0/SLE_12/x86_64/fio-2.2.5-1.1.x86_64.rpm")
    
               
    def test10_ValidateCephStatus(self):
        time.sleep(10)
        fsid = monitoring.getFSID()
        status = monitoring.getCephStatus()
        if fsid not in status:
            raise Exception, "fsid %s was not found in ceph status %s"\
                              % (fsid,status)
        active_clean = False
        counter = 0
        #default_pgs = str(self.ctx['default_pgs']).strip()
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
            log.info('cluster health is OK and PGs are active+clean') 
    
    
    def test11_fioPerformanceTests(self):
        LE = general.ListExceptions() #creating this object to track exceptions in child threads 
        job_list = []
        for fio_job in self.ctx['fio_jobs']:
            job_list.append(Thread(target=general.runfioJobs, args=(LE,), kwargs=fio_job))
        for job in job_list:
            job.start()
        for thread in threading.enumerate():
            if thread is not threading.currentThread():
                thread.join()
        assert(len(LE.exceptionList) < 1), TE.exceptionList


    
    def tearDown(self):
        log.info('++++++completed %s ++++++' % self._testMethodName)
        
        
         
    @classmethod
    def teardown_class(self):
        general.printRPMVersionsISO(self.ctx['iso_build_num'])
        after_cleanup = os.environ.get("AFTER_CLEANUP")
        if after_cleanup == None:
            log.info('skipping teardown for after_cleanup')
            return
        log.info('++++++++++++++starting teardown_class+++++++++++++')
        cephdeploy.cleanupNodes(self.ctx['allnodes'], 
                               'ceph')
        log.info('++++++++++++++Completed teardown_class++++++++++++')
