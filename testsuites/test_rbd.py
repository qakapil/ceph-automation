from utils import basetest
from utils import zypperutils
from utils import monitoring
from utils import general
from utils import rbd_operations
import logging,time,re, os, sys
from nose.exc import SkipTest


log = logging.getLogger(__name__)


def load_config(cls):
    filename = os.environ.get("CFG_FILE", "setup.cfg")
    cls.fetchIniData(cls, filename)
    yamlfile = os.environ.get("YAMLDATA_FILE")
    if yamlfile == None:
        yamlfile = __name__.split('.')[len(__name__.split('.'))-1]
        yamlfile = 'yamldata/%s.yaml' % (yamlfile)
    cls.fetchTestYamlData(cls,yamlfile)
    cls.setLogger(cls,'cephauto.log')
    os.environ["CLIENTNODE"] = cls.ctx['clientnode'][0]
    monitoring.printRPMVersions(cls.config.get('env','repo_baseurl'))

    url = cls.config.get('env','repo_baseurl')
    for node in cls.ctx['allnodes']:
        zypperutils.addRepo('ceph', url, node)


    before_cleanup = os.environ.get("BEFORE_CLEANUP")
    if before_cleanup != None:
        log.info('starting teardown for before_cleanup')
        #cephdeploy.cleanupNodes(cls.ctx['allnodes'], 'ceph')
        general.perNodeCleanUp(cls.ctx['allnodes'], 'ceph')

def setUp(self):
    ?run_prerequisits?
    check_installation
    check_module
    check_rbd_sanity


def test_image(self):
    create_images(self)
    validate_images(self)
    resize_images(self)
    validate_images(self)
    remove_images(self)
    validate_images(self)


def test_snapshot(self):
    create_snapshot(self)
    validate_snapshot_presence(self, True)
    validate_snapshot_diff(self, False)
    make_changes_to_image(self)
    validate_snapshot_diff(self, True)
    rollback_snapshot(self)
    validate_snapshot_diff(self, False)
    create_snapshot(self)
    validate_snapshot_presence(self)
    # validate_snapshot_diff(self, False) but not all.. how to prevent ? give single params instead of the whole dict? bad!
    purge_snapshot(self)
    validate_snapshot_presence(self, False)
    pass

def test_qemu(self):
    qemu_img_create(self)
    qemu_img_validate(self)
    qemu_img_resize(self)
    qemu_img_validate(self)
    qemu_img_convert(self)
    qemu_img_validate
    pass

def test_map_image(self):
    create_image(self)
    validate_image(self)
    map_image(self)
    show_mapped(self)
    unmap(self)


# Image Operations
def create_images(self):
    for image in self.ctx['images']:
        rbd_operations.createRBDImage(image)

def resize_images(self):
    for image in self.ctx['images']:
        rbd_operations.resizeRBDImage(image)

def remove_images(self):
    for image in self.ctx['images']:
        rbd_operations.rbdRemovePoolImage(image)

def validate_images(self):
    for image in self.ctx['images']:
        rbd_operations.validate_image_size(image)


# Snapshots

def rollback_snapshot(self):
    for snapshot in self.ctx['snapshot']:
        rbd_operations.rollback_snapshot(snapshot)


def create_snapshot(self):
    for snapshot in self.ctx['snapshot']:
        rbd_operations.create_snapshot(snapshot)


def purge_snapshot(self):
    for snapshot in self.ctx['snapshot']:
        rbd_operations.create_snapshot(snapshot)

def validate_snapshot_presence(self):
    for snapshot in self.ctx['snapshot']:
        rbd_operations.validate_snapshot(snapshot)

def validate_snapshot_diff(self, expected_difference):
    for snapshot in self.ctx['snapshot']:
        rbd_operations.validate_snapshot_diff(snapshot, expected_difference)


# Qemu


# Mapping

def map_images(self):
    for image in self.ctx['images']:
        rbd_operations.mapImage(image)

def show_mapped_images(self):
    for image in self.ctx['images']:
        rbd_operations.showmapped_images(image)

def unmap_images(self):
    for image in self.ctx['images']:
        rbd_operations.unmap_images(image)



def tearDown(self):
    log.info('++++++completed %s ++++++' % self._testMethodName)
