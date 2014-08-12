from utils import basetest
from utils import zypperutils
from utils import cephdeploy
from utils import general
from utils import monitoring_fork as monitoring
from utils import operations
import logging,time,re
from utils.launch import launch

#from nose import with_setup

log = logging.getLogger(__name__)



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

class TestCeph(basetest.Basetest):
    
    
    
    def initialise(self):
        #self.log.error(self.ctx.keys())
        if not self.ctx.has_key('workingdir'):
            self.ctx['workingdir'] = '~/cephdeploy-cluster'

    def system_buildup(self):
        uri_repo = self.config.get('env','repo_baseurl')
        #self.log.error("url=%s" % (url))
        uri_sig = "http://download.suse.de/ibs/Devel:/Storage:/1.0:/Staging/SLE_12/repodata/repomd.xml.key"
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
        self.log.error("self.ctx['osds']=%s" % (self.ctx['osds']))
        self.log.error("self.ctx['workingdir']=%s" % (self.ctx['workingdir']))
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
        zypperutils.removePkg('ceph-deploy')
    
    def setUp(self):
        
        log.info('++++++starting %s ++++++' % self._testMethodName)
        self.fetchIniData(self)
        self.setLogger(self)
        self.fetchTestYamlData(self,__name__)
        self.log = logging.getLogger("TestCeph")
        self.system_tear_down()
        self.initialise()
        self.system_buildup()
        
        
    def tearDown(self):
        self.log.info('++++++completed %s ++++++' % self._testMethodName)
        self.system_tear_down()
    
    def test_disgnostics(self):
        mon_node = self.ctx['mon_node']
        check_health(mon_node)
        repo_baseurl = self.config.get('env','repo_baseurl')
        check_CephDeployVersion(mon_node,repo_baseurl)
    
