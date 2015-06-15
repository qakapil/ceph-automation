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
 

    def test01_ISCSI(self):
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
            iscsi.createFSMount(iscsi_target['client_node'], drive, 'xfs', self.ctx['test_dir'])


    def test02_fio(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/fio.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/fio.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/fio.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)


    def test03_bonnie(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/bonnie.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/bonnie.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/bonnie.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)

    def test04_fsx(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/fsx.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/fsx.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/fsx.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)

    def test05_blogbench(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/blogbench.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/blogbench.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/blogbench.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)

    def test06_dbenchshort(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/dbench-short.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/dbench-short.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/dbench-short.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)



    def test07_dbench(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/dbench.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/dbench.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/dbench.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)

 

    def test08_ffsb(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/ffsb.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/ffsb.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/ffsb.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)
       

    

    def test09_fsstress(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/fsstress.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/fsstress.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/fsstress.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)


    def test10_pjd(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/pjd.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/pjd.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/pjd.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)

    def test11_iogen(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/iogen.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/iogen.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/iogen.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)

    def test12_iozone(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/iozone.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/iozone.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/iozone.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)

    def test13_iozonesync(self):
        cmd = 'ssh %s rm -rf %s/*' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s "cd -- %s && wget https://github.com/SUSE/ceph/raw/%s/qa/workunits/suites/iozone-sync.sh"' \
              % ( os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'])
        general.eval_returns(cmd)

        cmd = 'ssh %s sudo chmod 755 %s/iozone-sync.sh' % (os.environ["CLIENTNODE"], self.ctx['test_dir'])
        general.eval_returns(cmd)

        cmd = 'ssh %s "cd -- %s && CEPH_CLI_TEST_DUP_COMMAND=1 CEPH_REF=%s TESTDIR="%s" CEPH_ID="0" %s/iozone-sync.sh"' \
              % (os.environ["CLIENTNODE"], self.ctx['test_dir'], self.ctx['ceph_branch'], self.ctx['test_dir'], self.ctx['test_dir'])
        general.eval_returns(cmd)

    def test14_ISCSICLEANUP(self):
        for iscsi_target in self.ctx['iscsi_targets']:
            iscsi.cleanupISCSI(iscsi_target['client_node'], iscsi_target['node'], iscsi_target['iqn'], \
                               '3260', iscsi_target['block_name'], iscsi_target['rbd_mapped_disk'])

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
