from utils import basetest
from utils import zypperutils
from utils import cephdeploy
from utils import general
from utils import monitoring
from utils import operations
import logging,time,re
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
                                'ceph', cls.ctx['workingdir'])
    
    
      
    def test00_createDirs(self):
        log.info('++++++++++starting test0_createDirs++++++++++++++')
        if not self.ctx.has_key('workingdir'):
            self.ctx['workingdir'] = '~/cephdeploy-cluster'
        general.createDir(self.ctx['workingdir'])
        """
        for node in self.ctx['allnodes']:
            general.createDir('/var/lib/ceph/osd',node)
            general.createDir('/var/lib/ceph/bootstrap-osd',node)
        log.info('++++++++++Completed test0_createDirs+++++++++++++')
        """
    
    
    def test01_AddRepo(self):
        log.info('++++++++++starting test1_AddRepo+++++++++++++++++')
        url = self.config.get('env','repo_baseurl')
        zypperutils.addRepo('ceph', url)
        log.info('++++++++++Completed test1_AddRepo++++++++++++++++')
    
    
    def test02_InstallCephDeploy(self):
        log.info('++++++++++starting the test test2_InstallCephDeploy\
                  +++++++++++++++')
        zypperutils.installPkg('ceph-deploy')
        log.info('+++++++++++++++Completed test2_InstallCephDeploy\
                  +++++++++++++++')
    
    
    def test03_DeclareInitialMons(self):
        log.info('+++++++++++++++++starting test3_DeclareInitialMons \
                 ++++++++++++++++++')
        cephdeploy.declareInitialMons(self.ctx['initmons'], 
                                      self.ctx['workingdir'])
        log.info('+++++++++++++++++Completed test3_DeclareInitialMons \
                  +++++++++++++++++')
    
    
    
    def test04_InstallCeph(self):
        log.info('++++++++++++starting test4_installCeph+++++++++++++')
        cephdeploy.installNodes(self.ctx['allnodes'], 
                                self.ctx['workingdir'],
                                self.config.get('env','repo_baseurl'),
                                self.config.get('env','gpg_url'))
        log.info('++++++++++++Completed test4_installCeph++++++++++++')
        
    
    
    def test05_CreateInitialMons(self):
        log.info('+++++++++starting test5_createInitialMons+++++++++')
        cephdeploy.createInitialMons(self.ctx['initmons'], 
                                     self.ctx['workingdir'])
        log.info('+++++++++Completed test5_createInitialMons++++++++')
    
    
    
    def test06_PrepareActivateOSDs(self):
        log.info('+++++++++starting test6_PrepareActivateOSDs++++++++')
        cephdeploy.PrepareActivateOSDs(self.ctx['osds'], 
                                       self.ctx['workingdir'])
        log.info('+++++++++Completed test6_PrepareActivateOSDs+++++++')
    
    
    
    def test07_AdminNodes(self):
        log.info('++++++++++starting test7_AdminNodes++++++++++++++++')
        cephdeploy.addAdminNodes(self.ctx['allnodes'], 
                                 self.ctx['workingdir'])
        log.info('++++++++++completed test7_AdminNodes+++++++++++++++')
    
    
    
    def test08_ValidateCephStatus(self):
        log.info('++++++++++starting test8_ValidateCephStatus+++++++')
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
        log.info('+++++++++completed test8_ValidateCephStatus++++++++')
    
    
    
    def test09_ValidateCephDeployVersion(self):
        log.info('+++++++++starting test9_ValidateCephVersion++++++++')
        expVersion = cephdeploy.getExpectedVersion(
                                self.config.get('env','repo_baseurl'))
        actVersion = cephdeploy.getActuaVersion()
        if expVersion not in actVersion:
            raise Exception, "expected '%s' and actual '%s' versions \
                              did not match" % (expVersion,actVersion)
        log.info('++++++++completed test9_ValidateCephVersion++++++++')
     
    
    
    def test10_ValidateCephVersion(self):
        log.info('++++++++++++++++starting test10_ValidateCephVersion\
                  ++++++++++++++++')
        expVersion = monitoring.getExpectedVersion(
                     self.config.get('env','repo_baseurl'))
        actVersion = monitoring.getActuaVersion()
        if actVersion not in expVersion:
            raise Exception, "expected '%s' and actual '%s' \
                versions did not match" % (expVersion,actVersion)
        log.info('++++++++++++++++completed test10_ValidateCephVersion\
                  ++++++++++++++++')
    
    def test11_ValidateDefaultPools(self):
        log.info('+++++++++starting test11_ValidateDefaultPools++++++++')
        def_pools = monitoring.getDefaultPools()
        assert ('0 data,1 metadata,2 rbd,' in def_pools),"The default \
        pools were %s" % def_pools
        log.info('++++++++completed test11_ValidateDefaultPools++++++++')
     
    def test12_CreateImages(self):
        log.info('+++++++++starting test12_CreateImages++++++++')
        for image in self.ctx['images']:
            operations.createRBDImage(image)
        log.info('+++++++++completed test12_CreateImages++++++++')
    
    def test13_RemoveImages(self):
        log.info('+++++++++starting test05_RemoveImages++++++++')
        for image in self.ctx['images']:
            operations.rbdRemovePoolImage(image)
        log.info('+++++++++completed test05_RemoveImages++++++++')

    def test14_ValidateMonStat(self):
        log.info('+++++++++starting test13_ValidateMonStat++++++++')
        mon_stat = monitoring.getMonStat()
        log.info("the mon stat is "+ str(mon_stat))
        matchObj = re.match( r'.*:(.*) mons at .* quorum (.*?) (.*)', mon_stat, re.M|re.I)
        assert(len(self.ctx['initmons']) == int(matchObj.group(1))),\
        "the number of mons active were not as expected"
        assert(len(self.ctx['initmons']) == len(matchObj.group(2).split(','))),\
        "the number of mons in quorum were not as expected"
        assert(self.ctx['initmons'] == matchObj.group(3).split(',')),\
        "the monlist in quorum was not as expected"
        log.info('+++++++++completed test13_ValidateMonStat+++++++')

    
    def test15_ValidateOSDStat(self):
        log.info('+++++++++starting test14_ValidateOSDStat++++++++')
        osd_stat = monitoring.getOSDStat()
        n = len(self.ctx['osds'])
        expStr = "%s osds: %s up, %s in" % (n,n,n)
        assert(expStr in osd_stat),"osd stat validation failed"
        log.info('+++++++++completed test14_ValidateOSDStat+++++++') 
    
    def test16_RadosObjects(self):
        log.info('+++++++++starting test15_RadosObjects++++++++')
        for radosobject in self.ctx['radosobjects']:
            operations.createValidateObject(radosobject)
        for radosobject in self.ctx['radosobjects']:
            operations.removeObject(radosobject)
        log.info('+++++++++completed test15_RadosObjects++++++++')
    
    
       
    def test17_CreatePools(self):
        log.info('+++++++++starting test16_CreatePools++++++++')
        for pool in self.ctx['createpools']:
            operations.createPool(pool)
        log.info('+++++++++completed test16_CreatePools++++++++')
        
    def test18_ValidatePools(self):
        log.info('+++++++++starting test17_ValidatePools++++++++')
        for pool in self.ctx['createpools']:
            operations.validatePool(pool)
        log.info('+++++++++completed test17_ValidatePools++++++++')
    
    def test19_DeletePools(self):
        log.info('+++++++++starting test10_DeletePools++++++++')
        for pool in self.ctx['createpools']:
            operations.deletePool(pool)
        log.info('+++++++++completed test10_DeletePools++++++++')
    
    def test20_Validatelibrbd(self):
        log.info('+++++++++starting test18_Validatelibrbd++++++++')
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
        log.info('+++++++++completed test18_Validatelibrbd++++++++')
        
    
    def test21_ValidateDefaultOSDtree(self):
        log.info('+++++++++starting test11_ValidateDefaultOSDtree++++++++')
        str_osd_tree = monitoring.getOSDtree()
        osd_tree = str_osd_tree.split('\n')
        for i in range(len(osd_tree)-1):
            osd_tree[i] = osd_tree[i].split('\t')
        indx = osd_tree[0].index('weight')
        for i in range(len(osd_tree)-1):
            value = osd_tree[i][indx].strip()
            assert('0' != value),"the weight of the\
            osd was zero \n"+str_osd_tree
        log.info('+++++++++completed test11_ValidateDefaultOSDtree++++++++')

        
        
    """
    @classmethod
    def teardown_class(self):
        log.info('++++++++++++++starting teardown_class+++++++++++++')
        cephdeploy.cleanupNodes(self.ctx['allnodes'], 
                               'ceph', self.ctx['workingdir'])
        log.info('++++++++++++++Completed teardown_class++++++++++++')
    """
