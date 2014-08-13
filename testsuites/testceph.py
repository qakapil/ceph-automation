from utils import basetest
from utils import zypperutils
from utils import cephdeploy
from utils import general
from utils import monitoring_fork as monitoring
from utils import operations_fork as operations
import logging,time,re
from utils.launch import launch
#from utils import librbd_tasks
#from nose import with_setup
import os

log = logging.getLogger(__name__)

# Note:
# the following test enviroment variabels can be used:
# TEST_NOEARLYCLEANUP
# TEST_NOLATECLEANUP


# replacements of kapil's methods

def osd_prepare(listOSDs, strWorkingdir):
    # forked as takes different inputs from osd_activate
    for osd in listOSDs:
        cmd = 'ceph-deploy osd prepare --zap %s' % (osd)
        rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

def osd_activate(listOSDs, strWorkingdir):
    # forked as takes different inputs from osd_prepare
    for osd in listOSDs:
        cmd = 'ceph-deploy osd activate %s' % (osd)
        rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

def getFSID(node):
    # forked as ceph local node is not part of cluster and must run on node
    cmd = 'ssh %s sudo ceph-conf --lookup fsid' % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    fsid = stdout.strip()
    log.info('ceph fsid is - '+fsid)
    return fsid

def getCephStatus(node):
    # forked as ceph local node is not part of cluster and must run on node
    cmd = 'ssh %s sudo ceph --status'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    log.info('ceph status is - '+stdout)
    return stdout.strip()

# collection of tests scripts.


def check_health(node):
    log = logging.getLogger("check_health")
    fsid = getFSID(node)
    status = monitoring.getCephStatus(node)
    if fsid not in status:
        raise Exception, "fsid %s was not found in ceph status %s"\
                          % (fsid,status)
    active_clean = False
    counter = 0
    #default_pgs = str(self.ctx['default_pgs']).strip()
    default_pgs = monitoring.getTotalPGs(node)
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
        status = monitoring.getCephStatus(node)
    if 'health HEALTH_WARN clock skew detected' in status:
        log.warning('health HEALTH_WARN clock skew detected in\
                     ceph status')
    if 'health HEALTH_OK' in status:
        log.warning('cluster health is OK and PGs are active+clean')


def check_CephDeployVersion(node,repo_baseurl):
    log = logging.getLogger("check_CephDeployVersion")
    expVersion = cephdeploy.getExpectedVersion(repo_baseurl)
    actVersion = cephdeploy.getActuaVersion()
    log.debug("actVersion=%s" % (actVersion))
    if actVersion not in expVersion:
        raise Exception, "expected '%s' and actual '%s' versions \
                          did not match" % (expVersion,actVersion)

def check_DefaultPools(node):
    log = logging.getLogger("check_DefaultPools")
    def_pools = monitoring.getPoolList(node)
    assert ('0 data,1 metadata,2 rbd,' in def_pools),"The default \
    pools were %s" % def_pools


def check_CreateDestroyImages(test_node, images):
    log = logging.getLogger("check_CreateImages")
    for image in images:
        operations.createRBDImage(test_node, image)
    for image in images:
        operations.rbdRemovePoolImage(test_node, image)

def check_ValidateMonStat(node, initmons):
    mon_stat = monitoring.getMonStat(node)
    log.info("the mon stat is "+ str(mon_stat))
    matchObj = re.match( r'.*:(.*) mons at .* quorum (.*?) (.*)', mon_stat, re.M|re.I)
    assert(len(initmons) == int(matchObj.group(1))),\
    "the number of mons active were not as expected"
    assert(len(initmons) == len(matchObj.group(2).split(','))),\
    "the number of mons in quorum were not as expected"
    assert(sorted(initmons) == sorted(matchObj.group(3).split(','))),\
    "the monlist in quorum was not as expected"

def check_Pools(node, createpools):
    for pool in createpools:
        operations.createPool(node, pool)
    for pool in createpools:
        operations.validatePool(node, pool)
    for pool in createpools:
        operations.deletePool(node, pool)

def check_Validatelibrbd(librbd_images):
    log = logging.getLogger("check_CreateImages")
    try:
        from utils import librbd_tasks
    except ImportError, e:
        log.warning(e)
        return
    for image in librbd_images:
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


def check_ValidateDefaultOSDtree(node):
    str_osd_tree = monitoring.getOSDtree(node)
    osd_tree = str_osd_tree.split('\n')
    for i in range(len(osd_tree)-1):
        osd_tree[i] = osd_tree[i].split('\t')
    indx = osd_tree[0].index('weight')
    for i in range(len(osd_tree)-1):
        value = osd_tree[i][indx].strip()
        assert('0' != value),"the weight of the\
        osd was zero \n"+str_osd_tree


def check_InvalidDiskOSDPrepare(osds):
    rc = cephdeploy.prepareInvalidOSD(osds)
    assert (rc == 1), "OSD Prepare for invalid disk did not fail"

class TestCeph(basetest.Basetest):
    def __init__(self, *args, **kwargs):
        super(basetest.Basetest, self).__init__(*args, **kwargs)
        self.log = logging.getLogger("TestCeph")
        self.fetchIniData(self)
        self.setLogger(self)

        self.fetchTestYamlData(self,__name__)
        if not self.ctx.has_key('workingdir'):
            self.ctx['workingdir'] = '~/cephdeploy-cluster'
        self.flag_cleanup_early = False
        self.flag_cleanup_late = False
        test_earlycleanup = os.environ.get("TEST_NOEARLYCLEANUP")
        if test_earlycleanup == None:
            self.flag_cleanup_early = True
        test_cleanup_late = os.environ.get("TEST_NOLATECLEANUP")
        if test_cleanup_late == None:
            self.flag_cleanup_late = True

    def system_buildup(self):
        uri_repo = self.config.get('env','repo_baseurl')
        zypperutils.addRepo('ceph', uri_repo)
        zypperutils.installPkg('ceph-deploy')
        cephdeploy.declareInitialMons(self.ctx['initmons'],
            self.ctx['workingdir'])
        cephdeploy.installNodes(self.ctx['allnodes'],
            self.ctx['workingdir'],
            self.config.get('env','repo_baseurl'),
            self.config.get('env','gpg_url'))
        cephdeploy.createInitialMons(self.ctx['initmons'],
            self.ctx['workingdir'])
        osd_prepare(self.ctx['osds'],
            self.ctx['workingdir'])
        osd_activate(self.ctx['osds_activate'],
            self.ctx['workingdir'])
        cephdeploy.addAdminNodes(self.ctx['allnodes'],
            self.ctx['workingdir'])
        for node in self.ctx['allnodes']:
            operations.restartCeph(node)


    def system_tear_down(self):

        cephdeploy.cleanupNodes(self.ctx['allnodes'],
                                'ceph', self.ctx['workingdir'])
        try: # we shoudl not do this but module makes untyped exceptions.
            zypperutils.removePkg('ceph-deploy')
        except:
            pass
        
        
        for item in self.ctx['osds_activate']:
            splitLine = item.split(':')
            if len(splitLine) < 2:
                continue
            cmd = 'ssh %s sudo rm -rf /etc/ceph/  /var/lib/ceph/' % (splitLine[0])
            self.log.error("executing=%s" % cmd)
            rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
            if rc != 0:
                raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
            device_path = splitLine[1]
            if len(device_path) < 1:
                continue
            if device_path[0] != '/':
                device_path = "/dev/%s" % (device_path)
            cmd = 'ssh %s sudo mount' % (splitLine[0])
            rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
            if rc != 0:
                raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
            lines = stdout.split('\n')
            for line in lines:
                self.log.debug(line)

    def setUp(self):
        log.info('++++++starting %s ++++++' % self._testMethodName)
        if self.flag_cleanup_early:
            self.system_tear_down()
        self.system_buildup()


    def tearDown(self):
        self.log.info('++++++completed %s ++++++' % self._testMethodName)
        if self.flag_cleanup_late:
           self.system_tear_down()

    def test_disgnostics(self):
        mon_node = self.ctx['mon_node']
        check_health(mon_node)
        repo_baseurl = self.config.get('env','repo_baseurl')
        check_CephDeployVersion(mon_node, repo_baseurl)
        check_DefaultPools(mon_node)
        check_CreateDestroyImages(mon_node, self.ctx['images'])
        initmons = self.ctx['initmons']
        check_ValidateMonStat(mon_node, initmons)
        createpools = self.ctx['createpools']
        check_Pools(mon_node, createpools)
        librbd_images = self.ctx['librbd_images']
        check_Validatelibrbd(librbd_images)
        check_ValidateDefaultOSDtree(mon_node)
        osd_list = self.ctx['osds']
        check_InvalidDiskOSDPrepare(osd_list)
