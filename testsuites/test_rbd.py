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
    validate_images_size(self)
    validate_images_presence(self, True)
    resize_images(self)
    validate_images_size(self) #with resized values
    remove_images(self)
    validate_images_presence(self, False)


def test_snapshot(self):
    create_snapshot(self)
    validate_snapshot_presence(self, True)
    validate_snapshot_diff(self, False)
    # change the image somehow
    # right now the only way is to map, mkfs, mount, touch, diff!
    validate_snapshot_diff(self, True)
    rollback_snapshot(self)
    validate_snapshot_diff(self, False)
    purge_snapshot(self)
    validate_snapshot_presence(self, False)

def test_qemu(self):
    create_qemu_image(self)
    validate_qemu_image_presence(self)
    resize_qemu_image(self)
    validate_qemu_image_size(self)
    convert_qemu_image(self)
    qemu_img_validate

def test_map_image(self):
    create_image(self)
    validate_image(self)
    map_image(self)
    show_mapped(self)
    unmap(self)


# Qemu

def create_qemu_image():
    for image in ctx['images']:
        rbd_operations.create_qemu_image(image)

def validate_qemu_image_size():
    for image in ctx['images']:
        rbd_operations.validate_qemu_image_size(image)

def validate_qemu_image_presence():
    for image in ctx['image']:
        rbd_operations.validate_qemu_image_presence(image)

def validate_qemu_image_format():
    for image in ctx['image']:
        # Optional parameters are: format_to_expect
        # Default value = qcow2
        rbd_operations.validate_qemu_image_format(image)

def convert_qemu_image():
    for image in ctx['image']:
        # Optional parameters are: from_image_format, to_image_format
        # Default values are:
        # from_image_format = raw
        # to_image_format = qcow2
        rbd_operations.convert_qemu_image(image)


def resize_qemu_image():
    for image in ctx['image']:
        # Optional parameters are: size
        # Default value = 2000
        rbd_operations.resize_qemu_image(image)


def toggle_chaching():
    pass


def toggle_discard_trim():
    pass


def qemu_nbd():
    pass





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


def validate_images_presence(self, expected_presence):
    for image in self.ctx['images']:
        rbd_operations.validate_image_presence(image, expected_presence)


def validate_images_size(self):
    for image in self.ctx['images']:
        rbd_operations.validate_image_size(image)


# Snapshots


def create_snapshot(self):
    for snapshot in self.ctx['snapshot']:
        rbd_operations.create_snapshot(snapshot)


def rollback_snapshot(self):
    for snapshot in self.ctx['snapshot']:
        rbd_operations.rollback_snapshot(snapshot)


def purge_snapshot(self):
    for snapshot in self.ctx['snapshot']:
        rbd_operations.purge_snapshot(snapshot)


def validate_snapshot_presence(self, expected_presence):
    for snapshot in self.ctx['snapshot']:
        rbd_operations.validate_snapshot_presence(snapshot, expected_presence)


def validate_snapshot_diff(self, expected_difference):
    for snapshot in self.ctx['snapshot']:
        rbd_operations.validate_snapshot_diff(snapshot, expected_difference)


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
