from utils import basetest
from utils import zypperutils
from utils import cephdeploy
from utils import monitoring
from utils import operations
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
        cls.setLogger(cls)
        os.environ["CLIENTNODE"] = cls.ctx['clientnode']
        monitoring.printRPMVersions(cls.config.get('env','repo_baseurl'))
        before_cleanup = os.environ.get("BEFORE_CLEANUP")
        if before_cleanup != None:
            log.info('starting teardown for before_cleanup')
            cephdeploy.cleanupNodes(cls.ctx['allnodes'], 
                                    'ceph')
    
    def setUp(self):
        log.info('++++++starting %s ++++++' % self._testMethodName)

   
    
    def test01_AddRepo(self):
        url = self.config.get('env','repo_baseurl')
        zypperutils.addRepo('ceph', url)
    
    
    def test02_InstallCephDeploy(self):
        zypperutils.installPkg('ceph-deploy')
    
    
    def test03_DeclareInitialMons(self):
        cephdeploy.declareInitialMons(self.ctx['initmons'])
    
    
    
    def test04_InstallCeph(self):
        cephdeploy.installNodes(self.ctx['allnodes'],
                                self.config.get('env','repo_baseurl'),
                                self.config.get('env','gpg_url'))
        
    
    
    def test05_CreateInitialMons(self):
        cephdeploy.createInitialMons(self.ctx['initmons'])
    
    
    
    def test06_ZapOSDs(self):
        if self.ctx['osd_zap'] == None:
            log.info('No disks to zap. Skipping')
            return
        cephdeploy.osdZap(self.ctx['osd_zap'])
    
    
    def test07_PrepareOSDs(self):
        cephdeploy.osdPrepare(self.ctx['osd_prepare'])
    
    def test08_ActivateOSDs(self):
        cephdeploy.osdActivate(self.ctx['osd_activate'])
    
    
    def test09_AdminNodes(self):
        cephdeploy.addAdminNodes(self.ctx['allnodes'])
    
    
    def test10_restartCeph(self):
        for node in self.ctx['initmons']:
            operations.restartCeph(node)
        
        
    def test11_ValidateCephStatus(self):
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
    
    
    
    def test11_ValidateCephDeployVersion(self):
        expVersion = cephdeploy.getExpectedVersion(
                                self.config.get('env','repo_baseurl'))
        actVersion = cephdeploy.getActuaVersion()
        if actVersion not in expVersion:
            raise Exception, "expected '%s' and actual '%s' versions \
                              did not match" % (expVersion,actVersion)
     
    
    
    def test12_ValidateCephVersion(self):
        expVersion = monitoring.getExpectedVersion(
                     self.config.get('env','repo_baseurl'))
        actVersion = monitoring.getActuaVersion()
        if actVersion not in expVersion:
            raise Exception, "expected '%s' and actual '%s' \
                versions did not match" % (expVersion,actVersion)
    
    def test13_ValidateDefaultPools(self):
        def_pools = monitoring.getDefaultPools()
        assert ('0 data,1 metadata,2 rbd,' in def_pools),"The default \
        pools were %s" % def_pools
     
    def test14_CreateImages(self):
        for image in self.ctx['images']:
            operations.createRBDImage(image)
    
    def test15_RemoveImages(self):
        for image in self.ctx['images']:
            operations.rbdRemovePoolImage(image)

    def test16_ValidateMonStat(self):
        mon_stat = monitoring.getMonStat()
        log.info("the mon stat is "+ str(mon_stat))
        matchObj = re.match( r'.*:(.*) mons at .* quorum (.*?) (.*)', mon_stat, re.M|re.I)
        assert(len(self.ctx['initmons']) == int(matchObj.group(1))),\
        "the number of mons active were not as expected"
        assert(len(self.ctx['initmons']) == len(matchObj.group(2).split(','))),\
        "the number of mons in quorum were not as expected"
        assert(sorted(self.ctx['initmons']) == sorted(matchObj.group(3).split(','))),\
        "the monlist in quorum was not as expected"

    
    def test17_ValidateOSDStat(self):
        osd_stat = monitoring.getOSDStat()
        n = len(self.ctx['osd_activate'])
        expStr = "%s osds: %s up, %s in" % (n,n,n)
        assert(expStr in osd_stat),"osd stat validation failed" 
    
    def test18_RadosObjects(self):
        for radosobject in self.ctx['radosobjects']:
            operations.createValidateObject(radosobject)
        for radosobject in self.ctx['radosobjects']:
            operations.removeObject(radosobject)
    
    
       
    def test19_CreatePools(self):
        for pool in self.ctx['createpools']:
            operations.createPool(pool)
        
    def test20_ValidatePools(self):
        for pool in self.ctx['createpools']:
            operations.validatePool(pool)
    
    def test21_DeletePools(self):
        for pool in self.ctx['createpools']:
            operations.deletePool(pool)
    
    def test22_Validatelibrbd(self):
        from utils import librbd_tasks
        for image in self.ctx['librbd_images']:
            cluster = librbd_tasks.createCluster('/etc/ceph/ceph.conf')
            log.info("created the cluster")
            pool_ctx = librbd_tasks.createPoolIOctx(image['poolname'],cluster)
            log.info("created the pool ctx")
            librbd_tasks.createImage(image['size_gb'],image['imagename'],pool_ctx)
            log.info("created the image")
            imageslist = librbd_tasks.getImagesList(pool_ctx)
            log.info("got the image list "+str(imageslist))
            assert(image['imagename'] in imageslist),"image %s could \
            was not created" %(image['imagename'])
            image_ctx = librbd_tasks.createImgCtx(image['imagename'], pool_ctx)
            log.info("created the image ctx")
            size = librbd_tasks.getImageSize(image_ctx)
            expsize = image['size_gb'] * 1024**3
            size = str(int(size)).strip()
            expsize = str(int(expsize)).strip()
            log.info('actual image size is '+size)
            log.info('expected image size is '+expsize)
            assert(size == expsize),"image size not as expected"
            stats = librbd_tasks.getImageStat(image_ctx)
            log.info("the stats for the image "+image['imagename']+\
            "are "+str(stats))
            librbd_tasks.close_imgctx(image_ctx)
            librbd_tasks.removeImage(pool_ctx, image['imagename'])
            log.info("removed the image")
            librbd_tasks.close_cluster(cluster, pool_ctx)
        
    
    def test23_ValidateDefaultOSDtree(self):
        str_osd_tree = monitoring.getOSDtree()
        osd_tree = str_osd_tree.split('\n')
        for i in range(len(osd_tree)-1):
            osd_tree[i] = osd_tree[i].split('\t')
        indx = osd_tree[0].index('weight')
        for i in range(len(osd_tree)-1):
            value = osd_tree[i][indx].strip()
            assert('0' != value),"the weight of the\
            osd was zero \n"+str_osd_tree

    
    def test24_InvalidDiskOSDPrepare(self): 
        rc = cephdeploy.prepareInvalidOSD(self.ctx['osd_activate'])
        assert (rc == 1), "OSD Prepare for invalid disk did not fail"
    
    
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
                               'ceph', self.ctx['workingdir'])
        log.info('++++++++++++++Completed teardown_class++++++++++++')
