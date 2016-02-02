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
        filename = os.environ.get("CFG_FILE", "SLE_12-iscsiMP.cfg")
        cls.fetchIniData(cls, filename)
        yamlfile = os.environ.get("YAMLDATA_FILE")
        if yamlfile is None:
            yamlfile = __name__.split('.')[len(__name__.split('.'))-1]
            yamlfile = 'yamldata/%s.yaml' % yamlfile
        cls.fetchTestYamlData(cls,yamlfile)
        cls.setLogger(cls,'cephauto-iscsiMP.log')

        os.environ["CLIENTNODE"] = cls.ctx['clientnode'][0]
    #----
        monitoring.printRPMVersions(cls.config.get('env','repo_baseurl'))
        general.removeOldRepos(cls.ctx['allnodes'], ['ceph-debug', 'ceph_extras'])   # 'home_dmdiss_libiscsi'])

        url = cls.config.get('env','repo_baseurl')
        #-- No working as it should. Not finding "libiscsi_repo_baseurl", in the "libiscsi"
        #-- which *it does* exist. So, having it manually/static *for now only* until we fix/understand it.
        #-- we ended up always with: http://dist.suse.de/install/SLP/SUSE-Enterprise-Storage-2.0-Alpha3/x86_64/DVD1/suse//
        #-- for the iscsi repo.
        '''
            [libiscsi]
            loglevel=debug
            libiscsi_repo_baseurl="http://download.opensuse.org/repositories/home:/dmdiss:/libiscsi/SLE_12/"
            libiscsi_gpg_url="http://download.opensuse.org/repositories/home:/dmdiss:/libiscsi/SLE_12/repodata/repomd.xml.key"
        '''
        #url_lib_iscsi = cls.config.get('libiscsi','libiscsi_repo_baseurl')
        url_lib_iscsi = "http://download.opensuse.org/repositories/home:/dmdiss:/libiscsi/SLE_12/"
        url_lrbd_repo = "http://download.suse.de/ibs/Devel:/Storage:/2.0:/Staging/SLE12/noarch/"


        for node in cls.ctx['allnodes']:
            zypperutils.addRepo('ceph', url, node)
            zypperutils.addRepo('home_dmdiss_libiscsi', url_lib_iscsi, node)

        before_cleanup = os.environ.get("BEFORE_CLEANUP")
        if before_cleanup is not None:
            log.info('starting teardown for before_cleanup')
            general.perNodeCleanUp(cls.ctx['allnodes'], 'ceph')
            general.perNodeCleanUp(cls.ctx['allnodes'], 'home_dmdiss_libiscsi')

        #-- Ceph and libiscsi packages.
        zypperutils.installPkg('ceph-deploy', os.environ["CLIENTNODE"])
        #zypperutils.installPkg('ceph-deploy', os.environ["CLIENTNODE"])
        zypperutils.installPkg('libiscsi-test', os.environ["CLIENTNODE"])
        zypperutils.installPkg('libiscsi-utils', os.environ["CLIENTNODE"])
        #-- iSCSI packages.
        zypperutils.installPkg('yast2-iscsi-lio-server', os.environ["CLIENTNODE"])
        zypperutils.installPkg('yast2-iscsi-client', os.environ["CLIENTNODE"])
        #zypperutils.installPkg('lrbd', os.environ["CLIENTNODE"])
        zypperutils.installPkg('targetcli', os.environ["CLIENTNODE"])

        cephdeploy.declareInitialMons(cls.ctx['initmons'])
        cephdeploy.installNodes(cls.ctx['allnodes'])
        cephdeploy.createInitialMons(cls.ctx['initmons'])
        cephdeploy.osdZap(cls.ctx['osd_zap'])
        cephdeploy.osdPrepare(cls.ctx['osd_prepare'])
        cephdeploy.osdActivate(cls.ctx['osd_activate'])
        cephdeploy.addAdminNodes(cls.ctx['clientnode'])
        cls.validateCephStatus()

        for image in cls.ctx['images']:
            rbd_operations.createRBDImage(image)
            rbd_operations.mapImage(image)
            ret_dict = rbd_operations.gather_device_names()
            rbd_operations.mkfs_for_image(ret_dict[image['name']])


        #--
        nictemplate_file = os.environ.get("NICTEMPLATE_FILE")
        if nictemplate_file is None:
            nictemplate_file = "nic-template"
            nictemplate_file = 'yamldata/%s' % nictemplate_file
        #cls.fetchIniData(cls, nictemplate_file)

        file_reader = open(nictemplate_file, "r")
        ifcfg_template = file_reader.read()
        file_reader.close()

        for iscsi_host in cls.ctx['iscsi_multipath_networking']:
            orig_ip = socket.gethostbyname(iscsi_host['node'])
            iscsi.addMultiPathNIC(iscsi_host['node'], iscsi_host['nic1'], iscsi_host['ipaddr_subnet1'], iscsi_host['gw1'], ifcfg_template)


    #--
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
            #time.sleep(5)
            time.sleep(10)
            counter += 1
            status = monitoring.getCephStatus()
        if 'health HEALTH_WARN clock skew detected' in status:
            log.warning('health HEALTH_WARN clock skew detected in\
                         ceph status')
        if 'health HEALTH_OK' in status:
            log.warning('cluster health is OK and PGs are active+clean')


    #-- This will setup the targets
    def test01_ISCSI_MP_SetupTargets(self):
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
            block = iscsi.discoverMultiPathLoginTarget(iscsi_target['client_node'], iscsi_target['node'], iscsi_target['iqn'], iscsi_target['tpg'], '3260')
            drive = iscsi.partitionIBlock(iscsi_target['client_node'], block)
            iscsi.createMultiPathFSMount(iscsi_target['client_node'], drive, 'xfs', self.ctx['test_dir'])
            #-- Adding the other NPs.
            for iscsi_host in self.ctx['iscsi_multipath_networking']:
                host_ip = socket.gethostbyname(iscsi_host['node'])
                #-- We need to --addnp for the added addresses.
                if iscsi_target['node'] == iscsi_host['node'] and iscsi_host['tgt_bind_all_addr'] == 'yes':
                    ipList = iscsi.listIPAddresses(iscsi_target['node'])
                    iscsi.addMultiPathNP(iscsi_target['node'], iscsi_target['iqn'], iscsi_target['tpg'], ipList, '3260')
            #--
            iscsi.generateDDFiles(iscsi_target['node'], self.ctx['test_dir'])
    #----

    #-- This will setup all the initiators.
    def test02_ISCSI_MP_SetupInitiators(self):
        for iscsi_initiator in self.ctx['iscsi_initiators']:
            initiator_ip = socket.gethostbyname(iscsi_initiator['node'])
            iscsi.iscsiService(iscsi_initiator['node'], 'start')
            iscsi.multipathService(iscsi_initiator['node'], 'start')
            discoveryList = ""
            for iscsi_target in self.ctx['iscsi_targets']:
                target_ip = socket.gethostbyname(iscsi_target['node'])
                discoveryList = iscsi.runDiscoveryOnInitiator(iscsi_initiator['node'], target_ip, '3260', iscsi_target['iqn'])
                iscsi.initiatorLoginAllTargets(iscsi_initiator['node'], discoveryList)
                iscsi.mountingPointOnInitiator(iscsi_initiator['node'], self.ctx['test_dir'], 'xfs', iscsi_target['node'])

            #--
            iscsi.listMultiPaths(iscsi_initiator['node'])

    #-- We will bring down a NIC on the target and check if the initiators still have access to files there.
    def test03_ISCSI_MP_Access(self):
        for iscsi_target in self.ctx['iscsi_targets']:
            nicDict = iscsi.dictNICsAndIPs(iscsi_target['node'])
            if not (len(nicDict) >= 2):
                raise Exception, "Not enough NICs/Addresses for ISCSI Multipath setup on %s" % (iscsi_target['node'])
            #-- We bring down every iface on target, test all initiators, then bring it up again.
            filesOnTarget = iscsi.listFilesOnMountingPoint(iscsi_target['node'], self.ctx['test_dir'])
            filesOnInitiator = []
            for iface in nicDict:
                #-- we don't want to kill our eth0, for now. All other ones, we will.
                if iface != 'eth0':
                    iscsi.disableIFace(iscsi_target['node'], iface)
                    for iscsi_initiator in self.ctx['iscsi_initiators']:
                        filesOnInitiator = iscsi.listFilesOnMountingPoint(iscsi_initiator['node'], self.ctx['test_dir'])

                    iscsi.enableIFace(iscsi_target['node'], iface)
                    for iscsi_host in self.ctx['iscsi_multipath_networking']:
                        #-- We need to get the gw to update routes.
                        if iscsi_target['node'] == iscsi_host['node']:
                            iscsi.updateRoutes(iscsi_target['node'], iface, iscsi_host['gw1'])

                    if (filesOnTarget != filesOnInitiator):
                        raise Exception, "The files listed on Target %s and Initiator %s for the mounting point %s don't match" % (iscsi_target['node'], iscsi_initiator['node'], self.ctx['test_dir'])


    #-- We will bring down a NIC on the initiator and check if the it still has access to files located at the target.
    def test04_ISCSI_MP_Access(self):
        for iscsi_initiator in self.ctx['iscsi_initiators']:
            nicDict = iscsi.dictNICsAndIPs(iscsi_initiator['node'])
            if not (len(nicDict) >= 2):
                raise Exception, "Not enough NICs/Addresses for ISCSI Multipath setup on %s" % (iscsi_initiator['node'])
            #-- We bring down every iface on initiator, test all targets, then bring it up again.
            filesOnInitiator = iscsi.listFilesOnMountingPoint(iscsi_initiator['node'], self.ctx['test_dir'])
            filesOnTarget = []
            for iface in nicDict:
                #-- we don't want to kill our eth0, for now. All other ones, we will.
                if iface != 'eth0':
                    iscsi.disableIFace(iscsi_initiator['node'], iface)
                    filesOnTarget = iscsi.listFilesOnMountingPoint(iscsi_initiator['target_node'], self.ctx['test_dir'])

                    iscsi.enableIFace(iscsi_initiator['node'], iface)
                    for iscsi_target in self.ctx['iscsi_multipath_networking']:
                        #-- We need to get the gw to update routes.
                        if iscsi_target['node'] == iscsi_initiator['node']:
                            iscsi.updateRoutes(iscsi_target['node'], iface, iscsi_target['gw1'])

                        if (filesOnTarget != filesOnInitiator):
                            raise Exception, "The files listed on Target %s and Initiator %s for the mounting point %s don't match" % (iscsi_target['node'], iscsi_initiator['node'], self.ctx['test_dir'])


#    def test14_ISCSICLEANUP(self):
#        for iscsi_target in self.ctx['iscsi_targets']:
#            iscsi.cleanupISCSI(iscsi_target['client_node'], iscsi_target['node'], iscsi_target['iqn'], \
#                               '3260', iscsi_target['block_name'], iscsi_target['rbd_mapped_disk'])

    def tearDown(self):
        log.info('++++++completed %s ++++++' % self._testMethodName)



    @classmethod
    def teardown_class(self):
        after_cleanup = os.environ.get("AFTER_CLEANUP")
        if after_cleanup == None:
            log.info('skipping teardown for after_cleanup')
            return
        log.info('++++++++++++++starting teardown_class+++++++++++++')
        cephdeploy.cleanupNodes(self.ctx['allnodes'], 'ceph')
        log.info('++++++++++++++Completed teardown_class++++++++++++')


