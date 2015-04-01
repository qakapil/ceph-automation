import logging
import general
import os, time


log = logging.getLogger(__name__)

#Images

def createRBDImage(dictImg):
    name = dictImg.get('name', None)
    size = dictImg.get('size', None)
    pool = dictImg.get('pool', 'rbd')
    imglist = rbdGetPoolImages(pool)
    if name in imglist:
        dct = gather_device_names(dictImg)
        unmap_image(dct[name])
        purge_snapshot(dictImg)
        rbdRemovePoolImage(dictImg)
    cmd = "ssh %s rbd create %s --size %s --pool %s" % (os.environ["CLIENTNODE"], name, size, pool)
    general.eval_returns(cmd)

def resizeRBDImage(dictImg, new_size=1250):
    name = dictImg.get('name', None)
    size = dictImg.get('size', 1250)
    pool = dictImg.get('pool', 'rbd')
    cmd = "ssh %s rbd -p %s resize --image=%s --size=%s" % (os.environ["CLIENTNODE"], pool, name, new_size)
    general.eval_returns(cmd)
    log.info("resized image %s in pool %s with the new size of %s" % (name, pool, new_size))

def rbdGetPoolImages(poolname):
    cmd = "ssh %s rbd -p %s ls" % (os.environ["CLIENTNODE"], poolname)
    stdout, strderr = general.eval_returns(cmd)
    return stdout.strip().split('\n')
    #maybe json?

def validate_image_size(dictImage, size=None):
    pool = dictImage.get('pool', None)
    name = dictImage.get('name', None)
    if size is None:
        size = dictImage.get('size', None)
    cmd = "ssh %s rbd -p %s --image %s info --format json" % (os.environ["CLIENTNODE"], pool, name)
    stdout, strderr = general.eval_returns(cmd)
    act_size_in_mb = (general.convStringToJson(stdout)['size']/1024/1024)
    assert (str(size) in str(act_size_in_mb)), "Error. Size for image %s was %s MB - expected it to be %s" \
                                               % (name, act_size_in_mb, size)
    log.info("validated image - %s in pool %s " % (name, pool))

def validate_image_presence(dictImage, expected_presence=True):
    poolname = dictImage.get('pool', None)
    imagename = dictImage.get('name', None)
    cmd = "ssh %s rbd -p %s ls --format json" % (os.environ["CLIENTNODE"], poolname)
    stdout, strderr = general.eval_returns(cmd)
    all_images = []
    stdout_list = general.convert_to_structure(stdout)
    for image in stdout_list:
        all_images.append(image)
    if expected_presence:
        assert (imagename in all_images), "Error, Image %s was not present" % imagename
    else:
        assert (imagename not in all_images), "Error. Image Should have not been in %s" % poolname


def rbdRemovePoolImage(dictImg):
    imgname = dictImg.get('name', None)
    poolname = dictImg.get('pool', 'rbd')
    cmd = "ssh %s rbd -p %s rm %s" % (os.environ["CLIENTNODE"], poolname, imgname)
    general.eval_returns(cmd)

## Mapping Images

def mapImage(dictImage):
    # is sudo required?
    #http://ceph.com/docs/master/rbd/rbd-ko/
    # ensure device is not mapped already
    # cant be sure even if after cleanup => before cleanup would be better!
    imagename = dictImage.get('name')
    pool = dictImage.get('pool', 'rbd')
    cmd = "ssh %s sudo rbd map %s/%s" % (os.environ["CLIENTNODE"], pool, imagename) #--id admin?
    general.eval_returns(cmd)


def gather_device_names(dictImage):
    pool = dictImage.get('pool', 'rbd')
    cmd = "ssh %s rbd -p %s showmapped --format json" % (os.environ["CLIENTNODE"], pool)
    stdout, strderr = general.eval_returns(cmd)
    stdout_json = general.convert_to_structure(stdout)
    properties = {}
    for props in stdout_json.values():
        properties.update({props['name']: props['device'].split('\\')[-1].replace('/', '')})
    return properties


def unmap_image(device=None):
    # Before unmapping ensure its unmounted
    assert (device != None), "Error no device provided"
    cmd = "ssh %s sudo rbd unmap /dev/%s" % (os.environ["CLIENTNODE"], device)
    general.eval_returns(cmd)


def unmount_image(device=None):
    assert (device != None), "Error no device provided"
    cmd = "ssh %s sudo umount /dev/%s" % (os.environ["CLEINTNODE"], device)
    general.eval_returns(cmd)


def mount_image(device=None, target=None):
    assert (device != None and target != None), "Error device or target not provided"
    # make sure target follows format of /%s
    # only execute this on the adm node
    cmd = "ssh %s sudo mkdir ~/%s" % (os.environ["CLIENTNODE"], target)
    general.eval_returns(cmd)
    cmd = "ssh %s sudo mount /dev/%s ~/%s" % (os.environ["CLIENTNODE"], device, target)
    general.eval_returns(cmd)


def write_to_mounted_image(target=None):
    assert (target != None), "Error target not provided"
    cmd = "ssh %s cd ~/%s && sudo chown jenkins:users %s && touch testfile_%s.txt && echo content > testfile_%s.txt" % \
          (os.environ["CLIENTNODE"], target, target, target, target)
    general.eval_returns(cmd)


def mkfs_for_image(device=None):
    assert (device != None), "Error no device provided"
    cmd = "ssh %s sudo mkfs.xfs /dev/%s" % (os.environ["CLEINTNODE"], device)
    general.eval_returns(cmd)


# Snapshots

def create_snapshot(dictSnaphot):
    poolname = dictSnaphot.get('pool', None)
    snapname = dictSnaphot.get('snapname', None)
    imagename = dictSnaphot.get('name', None)
    cmd = "ssh %s rbd -p %s snap create --snap %s %s" % (os.environ["CLIENTNODE"], poolname, snapname, imagename)
    general.eval_returns(cmd)


def list_snapshots(dictSnapshot):
    poolname = dictSnapshot.get('pool', None)
    imagename = dictSnapshot.get('name', None)
    cmd = "ssh %s rbd snap ls %s/%s --format json --pretty-format" % (os.environ["CLIENTNODE"], poolname, imagename)
    stdout, strderr = general.eval_returns(cmd)
    return general.convStringToJson(stdout)


def rollback_snapshot(dictSnapshot):
    # how to validate?
    poolname = dictSnapshot.get('pool', None)
    snapname = dictSnapshot.get('snapname', None)
    imagename = dictSnapshot.get('name', None)
    cmd = "ssh %s rbd snap rollback %s/%s@%s" % (os.environ["CLIENTNODE"], poolname, imagename, snapname)
    general.eval_returns(cmd)

    # purges all snapshots for a given image
def purge_snapshot(dictSnapshot):
    poolname = dictSnapshot.get('pool', None)
    imagename = dictSnapshot.get('name', None)
    cmd = "ssh %s rbd -p %s snap purge %s" % (os.environ["CLIENTNODE"], poolname, imagename)
    stdout, strderr = general.eval_returns(cmd)

    # removes a single snapshot
def remove_snapshot(dictSnapshot):
    poolname = dictSnapshot.get('pool', None)
    snapname = dictSnapshot.get('snapname', None)
    cmd = "ssh %s rbd -p %s snap rm --snap %s" % (os.environ["CLIENTNODE"], poolname, snapname)
    stdout, strderr = general.eval_returns(cmd)


def validate_snapshot_presence(dictSnapshot, expected_presence=True):
    poolname = dictSnapshot.get('pool', None)
    snapname = dictSnapshot.get('snapname', None)
    imagename = dictSnapshot.get('name', None)
    cmd = "ssh %s rbd -p %s snap ls %s --format json" %(os.environ["CLIENTNODE"], poolname, imagename)
    stdout, stderr = general.eval_returns(cmd)
    stdout_json = general.convert_to_structure(stdout)
    all_snaps = []
    for snap in stdout_json:
        all_snaps.append(snap['name'])
    if expected_presence:
        assert (snapname in all_snaps), "Error the snapshot %s you supposed to have is not present" % (snapname)
    else:
        # wrong?
        assert (snapname not in all_snaps), "Error the snapshot %s you supposed to have is not present" % (snapname)


def validate_snapshot_diff(dictSnapshot, expected_difference=False):
    poolname = dictSnapshot.get('pool', None)
    snapname = dictSnapshot.get('snapname', None)
    imagename = dictSnapshot.get('name', None)
    cmd = "ssh %s rbd -p %s diff %s --format json" %(os.environ["CLIENTNODE"], poolname, imagename)
    stdout, strderr = general.eval_returns(cmd)
    diff = general.convert_to_structure(stdout)
    print diff
    if expected_difference:
        assert (diff != []), "Error. No differences between image: %s and snapshot: %s" % (imagename, snapname)
    else:
        assert (diff == []), "Error. Differences between image: %s and snapshot: %s" % (imagename, snapname)

# Qemu

#1st ensure qemu is installed properly
# qemu-tools

def create_qemu_image(dictQemu, format='raw'):
    poolname = dictQemu.get('pool', None)
    imagename = dictQemu.get('name', None)
    size = dictQemu.get('size', None)
    imglist = rbdGetPoolImages(poolname)
    if imagename in imglist:
        purge_snapshot(dictQemu)
        rbdRemovePoolImage(dictQemu)
    cmd = "ssh %s qemu-img create -f %s rbd:%s/%s %s" % \
          (os.environ["CLIENTNODE"], format, poolname, imagename, size)
    general.eval_returns(cmd)
    # log.info('created qemu image %s') % imagename

def convert_qemu_image(dictQemu, from_format='raw', to_format='qcow2'):
    poolname = dictQemu.get('pool', None)
    imagename = dictQemu.get('name', None)
    size = dictQemu.get('size', None)
    physical_image = []  # TODO
    cmd = "ssh %s qemu-img convert -f %s -O %s %s rbd:%s/%s" % \
          (os.environ["CLIENTNODE"], from_format, to_format, physical_image, poolname, imagename)
    general.eval_returns(cmd)
    # log.info('converted the qemu image %s from % to %') % (imagename, from_format, to_format)

def resize_qemu_image(dictQemu, new_size=2000):
    poolname = dictQemu.get('pool', None)
    imagename = dictQemu.get('name', None)
    size = dictQemu.get('size', None)
    cmd = "ssh %s qemu-img resize rbd:%s/%s %s" % \
          (os.environ["CLIENTNODE"], poolname, imagename, size)
    general.eval_returns(cmd)
    # log.info('Resized the qemu image %s from % to %') % (imagename, size, new_size)

def validate_qemu_image_size(dictQemu):
    poolname = dictQemu.get('pool', None)
    imagename = dictQemu.get('name', None)
    size = dictQemu.get('size', None)
    cmd = "ssh %s qemu-img info rbd:%s/%s | sed -n '3p'" % (os.environ["CLIENTNODE"], poolname, imagename)
    stdout, strderr = general.eval_returns(cmd)
    act_size = stdout.split(' ')[2]
    assert (size != act_size), "Error. Size did not changed. Expected size: %s Actual Size: %s " % \
                               (size, act_size)


def validate_qemu_image_presence(dictQemu):
    poolname = dictQemu.get('pool', None)
    imagename = dictQemu.get('name', None)
    cmd = "ssh %s qemu-img info rbd:%s/%s" % (os.environ["CLIENTNODE"], poolname, imagename)
    stdout, strderr = general.eval_returns(cmd)


def validate_qemu_image_format(dictQemu, expected_format='qcow2'):
    poolname = dictQemu.get('pool', None)
    imagename = dictQemu.get('name', None)
    cmd = "ssh %s qemu-img info rbd:%s/%s | sed -n '2p'" %\
          (os.environ["CLIENTNODE"], poolname, imagename)
    stdout, strderr = general.eval_returns(cmd)
    actual_format = stdout.split(':')[-1].strip()
    assert (actual_format == expected_format), "Error. Expected format %s but found %s"\
                                               % (expected_format, actual_format)



#Misc

def benchmarking():
    pass


# snapshots TODO

def copy_move_etc():
    pass


def lock_snapshot(dictSnapshot):
    pass


def unprotect_snapshot(dictSnapshot):
    pass


def protect_snapshot(dictSnapshot):
    pass


def clone_snapshot(dictSnapshot):
    pass
