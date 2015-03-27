from utils import basetest
from utils import zypperutils
from utils import monitoring
from utils import general
from utils import baseconfig
from utils import rbd_operations
import logging,time,re, os, sys
from nose.exc import SkipTest


# log = logging.getLogger(__name__)
#
#
# filename = os.environ.get("CFG_FILE", "setup.cfg")
# cfg_data = baseconfig.fetchIniData(filename)
#
yamlfile = os.environ.get("YAMLDATA_FILE")
if yamlfile == None:
    yamlfile = __name__.split('.')[len(__name__.split('.'))-1]
    yamlfile = 'yamldata/%s.yaml' % (yamlfile)
yaml_data = baseconfig.fetchTestYamlData(yamlfile)
#
# baseconfig.setLogger('cephauto.log', cfg_data)
os.environ["CLIENTNODE"] = yaml_data['clientnode'][0]

# monitoring.printRPMVersions(cfg_data.get('env', 'repo_baseurl'))
# url = cfg_data.get('env', 'repo_baseurl')



#def setUp():
#    ?run_prerequisits?
#    check_installation
#    check_module
#   check_rbd_sanity


def test_image():
    create_images()
    validate_images_size()
    validate_images_presence(True)
    resize_images()
    validate_images_size() #with resized values
    remove_images()
    validate_images_presence(False)


def test_snapshot():
    create_snapshot()
    validate_snapshot_presence(True)
    validate_snapshot_diff(False)
    # change the image somehow
    # right now the only way is to map, mkfs, mount, touch, diff!
    validate_snapshot_diff(True)
    rollback_snapshot()
    validate_snapshot_diff(False)
    purge_snapshot()
    validate_snapshot_presence(False)

def test_qemu():
    create_qemu_image()
    validate_qemu_image_presence()
    resize_qemu_image()
    validate_qemu_image_size()
    convert_qemu_image()
    validate_qemu_image_format()

def test_map_image():
    create_images()
    # different image name here! Randomize imagenames! Randomize everything for max test coverage!
    validate_images_presence(True)
    map_images()
    show_mapped_images()
    unmap_images()

# Qemu

def create_qemu_image():
    for image in yaml_data['images']:
        rbd_operations.create_qemu_image(image)

def validate_qemu_image_size():
    for image in yaml_data['images']:
        rbd_operations.validate_qemu_image_size(image)

def validate_qemu_image_presence():
    for image in yaml_data['image']:
        rbd_operations.validate_qemu_image_presence(image)

def validate_qemu_image_format():
    for image in yaml_data['image']:
        # Optional parameters are: format_to_expect
        # Default value = qcow2
        rbd_operations.validate_qemu_image_format(image)

def convert_qemu_image():
    for image in yaml_data['image']:
        # Optional parameters are: from_image_format, to_image_format
        # Default values are:
        # from_image_format = raw
        # to_image_format = qcow2
        rbd_operations.convert_qemu_image(image)


def resize_qemu_image():
    for image in yaml_data['image']:
        # Optional parameters are: size
        # Default value = 2000
        rbd_operations.resize_qemu_image(image)


def toggle_caching():
    pass


def toggle_discard_trim():
    pass


def qemu_nbd():
    pass


# Image Operations

def create_images():
    for image in yaml_data['images']:
        rbd_operations.createRBDImage(image)


def resize_images():
    for image in yaml_data['images']:
        # Optional parameter are: size
        # Default size = 1250
        rbd_operations.resizeRBDImage(image)


def remove_images():
    for image in yaml_data['images']:
        rbd_operations.rbdRemovePoolImage(image)


def validate_images_presence(expected_presence):
    for image in yaml_data['images']:
        rbd_operations.validate_image_presence(image, expected_presence)


def validate_images_size():
    for image in yaml_data['images']:
        rbd_operations.validate_image_size(image)


# Snapshots


def create_snapshot():
    for snapshot in yaml_data['snapshot']:
        rbd_operations.create_snapshot(snapshot)


def rollback_snapshot():
    for snapshot in yaml_data['snapshot']:
        rbd_operations.rollback_snapshot(snapshot)


def purge_snapshot():
    for snapshot in yaml_data['snapshot']:
        rbd_operations.purge_snapshot(snapshot)


def validate_snapshot_presence(expected_presence):
    for snapshot in yaml_data['snapshot']:
        rbd_operations.validate_snapshot_presence(snapshot, expected_presence)


def validate_snapshot_diff(expected_difference):
    for snapshot in yaml_data['snapshot']:
        rbd_operations.validate_snapshot_diff(snapshot, expected_difference)


# Mapping

def map_images():
    for image in yaml_data['images']:
        rbd_operations.mapImage(image)


def show_mapped_images():
    for image in yaml_data['images']:
        rbd_operations.showmapped_images(image)


def unmap_images():
    for image in yaml_data['images']:
        rbd_operations.unmap_images(image)


def tearDown():
    pass
    # log.info('++++++completed %s ++++++')
