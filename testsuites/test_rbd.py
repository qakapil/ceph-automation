from utils import monitoring
from utils import operations
from utils import baseconfig
from ConfigParser import SafeConfigParser
import logging,time,re, os, sys

log = logging.getLogger(__name__)

cfg_data = None
yaml_data = {}


def setUp():
    global cfg_data
    global yaml_data
    filename = os.environ.get("CFG_FILE", "setup.cfg")
    cfg_data = SafeConfigParser()
    cfg_data.read(filename)

    yamlfile = os.environ.get("YAMLDATA_FILE")
    if yamlfile == None:
        yamlfile = __name__.split('.')[len(__name__.split('.'))-1]
        yamlfile = 'yamldata/%s.yaml' % (yamlfile)
    yaml_data = baseconfig.fetchTestYamlData(yamlfile)

    baseconfig.setLogger('cephauto.log', cfg_data)
    os.environ["CLIENTNODE"] = yaml_data['clientnode'][0]
    if not monitoring.isClusterReady(60):
        operations.createCephCluster(yaml_data, cfg_data)
    status = monitoring.isClusterReady(300)
    assert status is True, "Ceph cluster was not ready. Failing the test suite"


def test_image():
    create_images()
    # Images are created
    validate_images_size(None)
    # Assume the imagesize valid
    validate_images_presence(True)
    # Assume the image is present.
    resize_images()
    # Resize the image
    validate_images_size(1250) #with resized values # make it more generic
    # Check for correct imagesize
    remove_images()
    # Remove the image
    validate_images_presence(False)
    # Assume that the image is not present anymore

#
def test_snapshot():
    create_images()
    # Create a image to create a snapshot of
    create_snapshot()
    # Snapshot the newly created images
    validate_snapshot_presence(True)
    # Assume the snapshots are present
    validate_snapshot_diff(False)
    # Assume the snapshots and the image are not different
    # change the image somehow
    # right now the only way is to map, mkfs, mount, touch, diff!
    # validate_snapshot_diff(True)
    # After changing the image assume there is a difference
    rollback_snapshot()
    # Roll back the image
    validate_snapshot_diff(False)
    # Assume the snapshot is not different again
    purge_snapshot()
    # Purging all the snapshots attached to one specific image
    validate_snapshot_presence(False)
    # Assume the snapshot is not present anymore

def test_qemu():
    create_qemu_image()
    validate_qemu_image_presence()
    resize_qemu_image()
    validate_qemu_image_size()
    # convert_qemu_image() # missing physical image on machine
    # validate_qemu_image_format() depends on function above

def test_map_image():
    create_images()
    # different image name here! Randomize imagenames! Randomize everything for max test coverage! dont have to delete all over again
    validate_images_presence(True)
    # map_images() module not loaded cant continue testing
    # show_mapped_images() same here
    # unmap_images() same here

# Qemu

def create_qemu_image():
    for image in yaml_data['qemu']:
        rbd_operations.create_qemu_image(image)

def validate_qemu_image_size():
    for image in yaml_data['qemu']:
        rbd_operations.validate_qemu_image_size(image)

def validate_qemu_image_presence():
    for image in yaml_data['qemu']:
        rbd_operations.validate_qemu_image_presence(image)

def validate_qemu_image_format():
    for image in yaml_data['qemu']:
        # Optional parameters are: format_to_expect
        # Default value = qcow2
        rbd_operations.validate_qemu_image_format(image)

def convert_qemu_image():
    for image in yaml_data['qemu']:
        # Optional parameters are: from_image_format, to_image_format
        # Default values are:
        # from_image_format = raw
        # to_image_format = qcow2
        rbd_operations.convert_qemu_image(image)


def resize_qemu_image():
    for image in yaml_data['qemu']:
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


def validate_images_size(expected_size=None):
    for image in yaml_data['images']:
        rbd_operations.validate_image_size(image, expected_size)


# Snapshots


def create_snapshot():
    for snapshot in yaml_data['snapshots']:
        rbd_operations.create_snapshot(snapshot)


def rollback_snapshot():
    for snapshot in yaml_data['snapshots']:
        rbd_operations.rollback_snapshot(snapshot)


def purge_snapshot():
    for snapshot in yaml_data['snapshots']:
        rbd_operations.purge_snapshot(snapshot)


def validate_snapshot_presence(expected_presence):
    for snapshot in yaml_data['snapshots']:
        rbd_operations.validate_snapshot_presence(snapshot, expected_presence)


def validate_snapshot_diff(expected_difference):
    for snapshot in yaml_data['snapshots']:
        rbd_operations.validate_snapshot_diff(snapshot, expected_difference)


# Mapping

def map_images():
    for image in yaml_data['images']:
        rbd_operations.mapImage(image)


def unmap_images():
    for image in yaml_data['images']:
        for device in rbd_operations.gather_device_names(image):
            rbd_operations.unmap_image(device)


def tearDown():
    pass
    # log.info('++++++completed %s ++++++')
