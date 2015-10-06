from utils import basetest
from utils import zypperutils
from utils import rbd_operations
from utils import cephdeploy
from utils import monitoring
from utils import operations
from utils import general
import logging,time,re, os,threading,shutil
from threading import Thread
from datetime import datetime
from nose.plugins.skip import SkipTest

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
        general.removeOldxcdFiles()
        url = os.environ.get("ISO_URL")

        for node in cls.ctx['allnodes']:
            if os.environ.get("ISO1"):
                sMedia1 = general.downloadISOAddRepo(url, 'Media1', 'ceph', node, os.environ.get("ISO1"))
                media1_iso_name = os.environ.get("ISO1")
            else:
                sMedia1 = general.downloadISOAddRepo(url, 'Media1', 'ceph', node)
                media1_iso_name = 'SUSE-'+sMedia1+'-Media1.iso'
            if os.environ.get("ISO2"):
                sMedia2 = general.downloadISOAddRepo(url, 'Media2', 'ceph-debug', node, os.environ.get("ISO2"))
                media2_iso_name = os.environ.get("ISO2")
            else:
                sMedia2 = general.downloadISOAddRepo(url, 'Media2', 'ceph-debug', node)
                media2_iso_name = 'SUSE-'+sMedia2+'-Media2.iso'


        general.mount_extISO('/tmp/'+media1_iso_name, '/tmp/media1')
        general.mount_extISO('/tmp/'+media2_iso_name, '/tmp/media2')
        
        general.runXCDCHK(media1_iso_name, '/tmp/media1', 'Media1')
        general.runXCDCHK(media2_iso_name, '/tmp/media2', 'Media2')

        before_cleanup = os.environ.get("BEFORE_CLEANUP")
        if before_cleanup != None:
            log.info('starting teardown for before_cleanup')
            #cephdeploy.cleanupNodes(cls.ctx['allnodes'],'ceph', 'ceph-debug')
            general.perNodeCleanUp(cls.ctx['allnodes'], 'ceph')

        general.printISOurl(media1_iso_name, url)
    
    def setUp(self):
        if os.environ.get("CLUSTER_FAILED") == "Yes":
           raise SkipTest("ceph cluster was not active+clean")
        log.info('++++++starting %s ++++++' % self._testMethodName)

   
    

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
            zypperutils.installPkgFromRepo('fio', node, 'ceph')
            rbd_operations.enable_rbd_kernel_module(node)
            #general.installPkgFromurl(node, 
            #"http://download.suse.de/ibs/Devel:/Storage:/1.0/SLE_12/x86_64/fio-2.2.5-1.1.x86_64.rpm")
 
    def test10_ModifyPGNUM(self):
        operations.setPGNUM(self.ctx['set_pg_num'])  
               
    def test11_ValidateCephHealth(self):
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
            time.sleep(150)
            counter += 1
            status = monitoring.getCephStatus()
            if 'health HEALTH_WARN clock skew detected' in status:
                log.warning('health HEALTH_WARN clock skew detected in\
                             ceph status')
            if 'health HEALTH_OK' in status:
                health_ok = True
                log.warning('cluster health is OK and PGs are active+clean')
            else:
                #pass
                for node in self.ctx['initmons']:
                    operations.restartCeph(node)
    
   

    def test12_fioPerformanceTests(self):
        log.info('storing pre-run cluster info')
        general.storeClusterInfo('clusterinfo',before_run=True)

        log.info('starting fio jobs')
        LE = general.ListExceptions() #creating this object to track exceptions in child threads 
        job_list = []
        runtime_list = []
        for fio_job in self.ctx['fio_jobs']:
            job_list.append(Thread(target=general.runfioJobs, args=(LE,), kwargs=fio_job))
            runtime_list.append(int(fio_job['runtime']))
        max_runtime = max(runtime_list)+100
        for job in job_list:
            job.start()

        t = Thread(target=general.storeCephStatus, args=('clusterinfo',max_runtime-100,))
        t.start()

        for thread in threading.enumerate():
            if thread is not threading.currentThread():
                thread.join(max_runtime)

        log.info('finished fio jobs')
        log.debug('running threads '+str(threading.enumerate()))

        if len(threading.enumerate()) > 1:
            log.info("all threads not finished. Adding exception")
            LE.excList.append(threading.enumerate()[1:])
        log.info('storing post-run cluster info')
        general.storeClusterInfo('clusterinfo',before_run=False)

        i = datetime.now()
        archdir = i.strftime('%Y/%m/%d %H:%M:%S')
        archdir = archdir.replace("/","-").replace(" ","-").replace(":","-")
        archpath = os.path.join("/abuild/srv/www/htdocs/teuth-logs/perf-data/perf-data",archdir)
        clusterinfopath = os.path.join(archpath,"clusterinfo")
        shutil.copytree("clusterinfo", clusterinfopath)

        for fio_job in self.ctx['fio_jobs']:
            nodedir = clusterinfopath = os.path.join(archpath,'client-'+fio_job['node'])
            os.makedirs(nodedir)
            general.scpDir(fio_job['node'], 'perfjobs/fiojobs', nodedir)

        link = 'http://deacon.arch.suse.de/perf-data/perf-data/'+archdir
        f = open('report_url.txt', 'w')
        f.write('Performance Results: '+link+'\n')
        f.close()

        assert(len(LE.excList) < 1), LE.excList
    

    
    def tearDown(self):
        log.info('++++++completed %s ++++++' % self._testMethodName)
        
        
         
    @classmethod
    def teardown_class(self):
        #general.printRPMVersionsISO(self.ctx['iso_build_num'])
        after_cleanup = os.environ.get("AFTER_CLEANUP")
        if after_cleanup == None:
            log.info('skipping teardown for after_cleanup')
            return
        log.info('++++++++++++++starting teardown_class+++++++++++++')
        cephdeploy.cleanupNodes(self.ctx['allnodes'], 
                               'ceph', 'ceph-debug')
        log.info('++++++++++++++Completed teardown_class++++++++++++')
