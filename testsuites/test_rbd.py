from utils import monitoring
from utils import operations
from utils import baseconfig
from utils import rbd_operations
from utils import general
from utils import zypperutils
import inspect
from ConfigParser import SafeConfigParser
import logging
import os
import sys

log = logging.getLogger(__name__)

cfg_data = None
yaml_data = {}
vErrors = []


def setup_module():
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
    ceph_internal_url = cfg_data.get('env', 'ceph_internal_url')
    general.downloadISOAddRepo(ceph_internal_url, 'Media', 'ceph-internal',
                               os.environ["CLIENTNODE"], iso_name=None, iso_internal=True)
    for pkg in ['rbd-kmp-default','qemu-block-rbd','qemu-tools']:
        zypperutils.installPkgFromRepo(pkg, os.environ["CLIENTNODE"], 'ceph-internal')



def test_image():
    global vErrors
    try:
        delete_all_images()
        create_images_without_removal()
        # Images are created, dont remove old ones, none yet.
        validate_images_size(None)
        # Assume the imagesize valid
        validate_images_presence(True)
        # Assume the image is present.
        export_images()
        # Export all images
        import_images()
        # Import all images
        #export_image_diff()
        # Export the image diff
        #import_image_diff()
        # Import the image diff
        #lock_images()
        # Lock the images. Assume writing is not possible  TODO: MISSING TEST
        #unlock_images()
        # Unlocks the images. Assume writing is possible again.  TODO: MISSING TEST
        #copy_images()
        # Copy TODO: Make presence tests more generic to test file existence with pattern
        #move_images()
        # Move
        resize_images()
        # Resize the image
        validate_images_size(1250) #with resized values # make it more generic
        # Check for correct imagesize
        remove_images()
        # Remove the image
        validate_images_presence(False)
        # Assume that the image is not present anymore
    except:
        sError = str(sys.exc_info()[0])+" : "+str(sys.exc_info()[1])
        log.error(inspect.stack()[0][3] + "Failed with error - "+sError)
        vErrors.append(sError)
        raise sys.exc_info()[0], sys.exc_info()[1]


def test_qemu():
    global vErrors
    try:
        create_qemu_image()
        validate_qemu_image_presence()
        resize_qemu_image()
        validate_qemu_image_size()
        # convert_qemu_image() # missing physical image on machine
        # validate_qemu_image_format() depends on function above
    except:
        sError = str(sys.exc_info()[0])+" : "+str(sys.exc_info()[1])
        log.error(inspect.stack()[0][3] + "Failed with error - "+sError)
        vErrors.append(sError)
        raise sys.exc_info()[0], sys.exc_info()[1]


def test_snapshot():
    global vErrors
    try:
        create_images_without_removal()
        # Create a image to create a snapshot of
        create_snapshot()
        # Snapshot the newly created images
        validate_snapshot_presence(True)
        # Assume the snapshots are present
        validate_snapshot_diff(False)
        # Assume the snapshots and the image are not different
        map_images()
        # Map
        write_to_image()
        # Mkfs, Mount, write to image
        validate_snapshot_diff(True)
        # After changing the image assume there is a difference
        unmap_images()
        # Unmap
        rollback_snapshot()
        # Roll back the image
        validate_snapshot_diff(False)
        # Assume the snapshot is not different again
        purge_snapshot()
        # Purging all the snapshots attached to one specific image
        validate_snapshot_presence(False)
        # Assume the snapshot is not present anymore
        remove_images()
    except:
        sError = str(sys.exc_info()[0])+" : "+str(sys.exc_info()[1])
        log.error(inspect.stack()[0][3] + "Failed with error - "+sError)
        vErrors.append(sError)
        raise sys.exc_info()[0], sys.exc_info()[1]


def test_map_image():
    global vErrors
    try:
        create_images_without_removal()
        validate_images_presence(True)
        map_images()
        write_to_image()
        unmap_images()
    except:
        sError = str(sys.exc_info()[0])+" : "+str(sys.exc_info()[1])
        log.error(inspect.stack()[0][3] + "Failed with error - "+sError)
        vErrors.append(sError)
        raise sys.exc_info()[0], sys.exc_info()[1]


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

def delete_all_images():
    rbd_operations.delete_exported_images()
    for pool in rbd_operations.get_pool_names():
        for image in rbd_operations.images_in_pool(pool):
            rbd_operations.remove_image(pool, image)


def export_images():
    for image in yaml_data['images']:
        rbd_operations.export_image(image)


def import_images():
    for image in yaml_data['images']:
        rbd_operations.import_image(image)


def export_image_diff():
    for image in yaml_data['image']:
        rbd_operations.export_diff(image)


def import_image_diff():
    for image in yaml_data['image']:
        rbd_operations.import_diff(image)


def lock_images():
    for image in yaml_data['image']:
        rbd_operations.add_lock_to_image(image)


def unlock_images():
    for image in yaml_data['image']:
        ret_dct = rbd_operations.show_lock_of_image(image)
        rbd_operations.remove_lock_of_image(image, ret_dct.keys()[0], ret_dct.values()[0]['locker'])


def copy_images():
    for image in yaml_data['image']:
        rbd_operations.copy_image(image)


def move_images():
    for image in yaml_data['image']:
        rbd_operations.move_image(image)


def benchmarking():
    for image in yaml_data['images']:
        rbd_operations.benchmarking(image)


def create_images():
    for image in yaml_data['images']:
        rbd_operations.createRBDImage(image)


def create_images_without_removal():
    for image in yaml_data['images']:
        rbd_operations.create_rbd_image(image)


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


def show_children_of_snapshot():
    for snapshot in yaml_data['snapshots']:
        rbd_operations.children_for_snapshot(snapshot)


def protect_snapshots():
    # Not yet implemented
    for snapshots in yaml_data['snapshots']:
        rbd_operations.protect_snapshot(snapshots)


def unprotect_snapshot():
    # Not yet implemented
    for snapshots in yaml_data['snapshots']:
        rbd_operations.unprotect_snapshot(snapshots)


def clone_snapshot():
    # Not yet implemented
    for snapshot in yaml_data['snapshots']:
        rbd_operations.clone_snapshot(snapshot)


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


def write_to_image():
    for image in yaml_data['images']:
        # rbd_operations.createRBDImage(image)
        ret_dict = rbd_operations.gather_device_names()
        rbd_operations.mkfs_for_image(ret_dict[image['name']])
        rbd_operations.mount_image((ret_dict[image['name']]), image['name'])
        rbd_operations.write_to_mounted_image(image['name'])


def unmap_images():
    for image in yaml_data['images']:
        ret_dict = rbd_operations.gather_device_names()
        rbd_operations.unmount_image(ret_dict[image['name']])
        rbd_operations.unmap_image(ret_dict[image['name']])


def teardown_module():
    log.info('++++++completed rbd test suite ++++++')
    if vErrors:
        log.info('test suite failed with these errors - '+str(vErrors))
    else:
        log.info('starting teardown in teardown_module')
        general.perNodeCleanUp(yaml_data['allnodes'], 'ceph')
