from utils import basetest
from utils import zypperutils
from utils import cephdeploy
from utils import monitoring
from utils import general
from utils import iscsi
from utils import rbd_operations
import socket
import logging, time, os
from nose.exc import SkipTest

log = logging.getLogger(__name__)

class TestSanity(basetest.Basetest):

    @classmethod
    def setup_class(cls):
        filename = os.environ.get("CFG_FILE", "setup.cfg")    
        cls.fetchIniData(cls, filename)
        yamlfile = os.environ.get("YAMLDATA_FILE")
        if yamlfile is None:
            yamlfile = __name__.split('.')[len(__name__.split('.'))-1]
            yamlfile = 'yamldata/%s.yaml' % yamlfile
        cls.fetchTestYamlData(cls,yamlfile)
        cls.setLogger(cls,'cephauto.log')
        os.environ["CLIENTNODE"] = cls.ctx['clientnode'][0]
        monitoring.printRPMVersions(cls.config.get('env','repo_baseurl'))

        general.removeOldRepos(cls.ctx['allnodes'], ['ceph-debug', 'ceph_extras'])

        url = cls.config.get('env','repo_baseurl')
        for node in cls.ctx['allnodes']:
            zypperutils.addRepo('ceph', url, node)

        before_cleanup = os.environ.get("BEFORE_CLEANUP")
        if before_cleanup is not None:
            log.info('starting teardown for before_cleanup')
            general.perNodeCleanUp(cls.ctx['allnodes'], 'ceph')

        zypperutils.installPkg('ceph-deploy', os.environ["CLIENTNODE"])

        cephdeploy.declareInitialMons(cls.ctx['initmons'])

        cephdeploy.installNodes(cls.ctx['allnodes'])

        cephdeploy.createInitialMons(cls.ctx['initmons'])

        cephdeploy.osdZap(cls.ctx['osd_zap'])

        cephdeploy.osdPrepare(cls.ctx['osd_prepare'])

        cephdeploy.addAdminNodes(cls.ctx['clientnode'])

        cls.validateCephStatus()

        for image in cls.ctx['images']:
            rbd_operations.createRBDImage(image)
            rbd_operations.mapImage(image)


    def setUp(self):
        if os.environ.get("CLUSTER_FAILED") == "Yes":
           raise SkipTest("ceph cluster was not active+clean") 
        log.info('++++++starting %s ++++++' % self._testMethodName)

    @classmethod
    def validateCephStatus(cls):
        time.sleep(10)
        fsid = monitoring.getFSID()
        status = monitoring.getCephStatus()
        if fsid not in status:
            raise Exception, "fsid %s was not found in ceph status %s"\
                              % (fsid,status)
        active_clean = False
        counter = 0
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
            log.warning('cluster health is OK and PGs are active+clean')
 

    def test_ISCSI(self):
        for iscsi_target in self.ctx['iscsi_targets']:
            iscsi.targetService(iscsi_target['node'], 'start')
            iscsi.addBlock(iscsi_target['node'], iscsi_target['block_name'], iscsi_target['rbd_mapped_disk'])
            iscsi.addIQNTPG(iscsi_target['node'], iscsi_target['iqn'], iscsi_target['tpg'])
            ip = socket.gethostbyname(iscsi_target['node'])
            iscsi.addNP(iscsi_target['node'], iscsi_target['iqn'], iscsi_target['tpg'], ip, '3260')
            iscsi.disableAuth(iscsi_target['node'], iscsi_target['iqn'], iscsi_target['tpg'])
            iscsi.addLun(iscsi_target['node'], iscsi_target['iqn'], iscsi_target['tpg'], '0', 'MiddlingThingPort', iscsi_target['block_name'])
            iscsi.enableDemoMode(iscsi_target['node'], iscsi_target['iqn'], iscsi_target['tpg'])
            iscsi.enableTPG(iscsi_target['node'], iscsi_target['iqn'], iscsi_target['tpg'])
            iscsi.demoModeWriteProtect(iscsi_target['node'], iscsi_target['iqn'], iscsi_target['tpg'])

            block = iscsi.discoverLoginTarget(iscsi_target['client_node'], iscsi_target['node'], iscsi_target['iqn'], iscsi_target['tpg'], '3260')
            drive = iscsi.partitionIBlock(iscsi_target['client_node'], block)
            iscsi.createFSMount(iscsi_target['client_node'], drive, 'xfs')







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
                               'ceph')
        log.info('++++++++++++++Completed teardown_class++++++++++++')
