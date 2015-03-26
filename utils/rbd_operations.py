from launch import launch
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
        rbdRemovePoolImage(dictImg)
    cmd = "ssh %s rbd create %s --size %s --pool %s" % (os.environ["CLIENTNODE"], name, size, pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

def resizeRBDImage(dictImg, new_size=1250):
    name = dictImg.get('name', None)
    size = dictImg.get('size', 1250)
    pool = dictImg.get('pool', 'rbd')
    cmd = "ssh %s rbd -p %s resize --image=%s --size=%s" % (os.environ["CLIENTNODE"], pool, name, new_size)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("resized image %s in pool %s with the new size of %s" % (name, pool, new_size))

def rbdGetPoolImages(poolname):
    cmd = "ssh %s rbd -p %s ls" % (os.environ["CLIENTNODE"], poolname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    return stdout.strip().split('\n')
    #maybe json?

def validate_image_size(dictImage):
    poolname = dictImage.get('poolname', None)
    imagename = dictImage.get('imagename', None)
    size = dictImage.get('size_mb', None)
    cmd = "ssh %s rbd -p %s --image %s info --format json" % (os.environ["CLIENTNODE"], poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    act_size_in_mb = (general.convStringToJson(stdout)['size']/1024/1024)
    assert(str(size) in str(act_size_in_mb)), "Error. Size for image %s was %s MB" % (imagename, act_size_in_mb)
    log.info("validated image - %s in pool %s " % (imagename, poolname))

def validate_image_presence(dictImage, expected_presence=True):
    poolname = dictImage.get('poolname', None)
    imagename = dictImage.get('imagename', None)
    cmd = "ssh %s rbd -p %s ls --format json" % (os.environ["CLIENTNODE"], poolname)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    all_images = []
    for image in general.convStringToJson(stdout):
        all_images.append(image)
    if expected_presence:
        assert (imagename in all_images), "Error, Image %s was not present" % imagename
    else:
        assert (imagename not in all_images), "Error. Image Should have not been in %s" % poolname


def rbdRemovePoolImage(dictImg):
    imgname = dictImg.get('name', None)
    poolname = dictImg.get('pool', 'rbd')
    cmd = "ssh %s rbd -p %s rm %s" % (os.environ["CLIENTNODE"], poolname, imgname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

## Mapping Images

def mapImage(dictImage):
    # is sudo required?
    #http://ceph.com/docs/master/rbd/rbd-ko/
    imagename = dictImage.get('name')
    pool = dictImage.get('pool', 'rbd')
    cmd = "ssh %s rbd map %s/%s" % (os.environ["CLIENTNODE"], pool, imagename) #--id admin?
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing command %s. \
    Error message: %s" % (cmd, stderr)


def showmapped_images(dictImage):
    pool = dictImage.get('pool', 'rbd')
    cmd = "ssh %s rbd -p %s showmapped --format json" % (os.environ["CLIENTNODE"], pool)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing command %s. \
    Error message: %s" % (cmd, stderr)
    mapped_images = []
    count = 1
    for imagename in general.convStringToJson(stdout):
        mapped_images.append(imagename['%s']['name']) % count
        count += 1

def unmap_images(dictImage):
    # TBC
    # discover device, then unmap
    #rbd unmap /dev/rbd0
    # sudo rbd unmap /dev/rbd/{poolname}/{imagename}
    # sudo?
    pass


# Snapshots

def create_snapshot(dictSnaphot):
    poolname = dictSnaphot.get('poolname', None)
    snapname = dictSnaphot.get('snapname', None)
    imagename = dictSnaphot.get('imagename', None)
    cmd = "ssh %s rbd -p %s snap create --snap %s %s" % (os.environ["CLIENTNODE"], poolname, snapname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)


def list_snapshots(dictSnapshot):
    poolname = dictSnapshot.get('poolname', None)
    imagename = dictSnapshot.get('imagename', None)
    cmd = "ssh %s rbd snap ls %s/%s --format json --pretty-format" % (os.environ["CLIENTNODE"], poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    return general.convStringToJson(stdout)


def rollback_snapshot(dictSnapshot):
    # how to validate?
    poolname = dictSnapshot.get('poolname', None)
    snapname = dictSnapshot.get('snapname', None)
    imagename = dictSnapshot.get('imagename', None)
    cmd = "ssh %s rbd snap rollback %s/%s@%s" % (os.environ["CLIENTNODE"], poolname, imagename, snapname)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

    # purges all snapshots for a given image
def purge_snapshot(dictSnapshot):
    poolname = dictSnapshot.get('poolname', None)
    imagename = dictSnapshot.get('imagename', None)
    cmd = "ssh %s rbd -p %s snap purge %s" % (os.environ["CLIENTNODE"], poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

    # removes a single snapshot
def remove_snapshot(dictSnapshot):
    poolname = dictSnapshot.get('poolname', None)
    snapname = dictSnapshot.get('snapname', None)
    imagename = dictSnapshot.get('imagename', None)
    cmd = "ssh %s rbd -p %s snap rm --snap %s" % (os.environ["CLIENTNODE"], poolname, snapname)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)


def validate_snapshot_presence(dictSnapshot, expected_presence=True):
    poolname = dictSnapshot.get('poolname', None)
    snapname = dictSnapshot.get('snapname', None)
    imagename = dictSnapshot.get('imagename', None)
    cmd = "ssh %s rbd -p %s snap ls %s --format json" %(os.environ["CLIENTNODE"], poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    all_snaps = []
    for snap in general.convStringToJson(stdout):
        if snap in locals():
            all_snaps.append(snap['name'])
    if expected_presence:
        assert (snapname in all_snaps), "Error the snapshot %s you supposed to have is not present" % (snapname)
    else:
        # wrong?
        assert (snapname not in all_snaps), "Error the snapshot %s you supposed to have is not present" % (snapname)

def validate_snapshot_diff(dictSnapshot, expected_difference=False):
    poolname = dictSnapshot.get('poolname', None)
    snapname = dictSnapshot.get('snapname', None)
    imagename = dictSnapshot.get('imagename', None)
    cmd = "ssh %s rbd -p %s snap ls %s --format json" %(os.environ["CLIENTNODE"], poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    diff = general.convStringToJson(stdout)
    if expected_difference:
        assert (diff != []), "Error. No differences between image: %s and snapshot: %s" % (imagename, snapname)
    else:
        assert (diff == []), "Error. Differences between image: %s and snapshot: %s" % (imagename, snapname)
    log.info('validating snapshot diff of % with image: %s') % (snapname, imagename)


# Qemu

#1st ensure qemu is installed properly
# qemu-tools

def create_qemu_image(dictImage, format='raw'):
    poolname = dictImage.get('poolname', None)
    imagename = dictImage.get('imagename', None)
    size = dictImage.get('size', None)
    cmd = "ssh %s qemu-image create -f %s rbd:%s/%s %s" % \
          (os.environ["CLIENTNODE"], format, poolname, imagename, size)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info('created qemu image %s') % imagename


def convert_qemu_image(dictImage, from_format='raw', to_format='qcow2'):
    poolname = dictImage.get('poolname', None)
    imagename = dictImage.get('imagename', None)
    size = dictImage.get('size', None)
    physical_image = []  # TODO
    cmd = "ssh %s qemu-image convert -f %s -O %s %s rbd:%s/%s" % \
          (os.environ["CLIENTNODE"], from_format, to_format, physical_image, poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info('converted the qemu image %s from % to %') % (imagename, from_format, to_format)

def resize_qemu_image(dictImage, new_size=2000):
    poolname = dictImage.get('poolname', None)
    imagename = dictImage.get('imagename', None)
    size = dictImage.get('size', None)
    cmd = "ssh %s qemu-image resize rbd:%s/%s %s" % \
          (os.environ["CLIENTNODE"], poolname, imagename, size)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s. \
    Error message: %s" % (cmd, stderr)
    log.info('Resized the qemu image %s from % to %') % (imagename, size, new_size)

def validate_qemu_image_size(dictImage):
    poolname = dictImage.get('poolname', None)
    imagename = dictImage.get('imagename', None)
    size = dictImage.get('size', None)
    cmd = "ssh %s qemu-image info rbd:%s/%s | sed -n '3p'" % (os.environ["CLIENTNODE"], poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s. \
    Error message: %s" % (cmd, stderr)
    act_size = stdout.split(' ')[2]
    assert (size != act_size), "Error. Size did not changed. Expected size: %s Actual Size: %s " % \
                               (size, act_size)

#
#
def validate_qemu_image_presence(dictImage):
    poolname = dictImage.get('poolname', None)
    imagename = dictImage.get('imagename', None)
    cmd = "ssh %s qemu-image info rbd:%s/%s" % (os.environ["CLIENTNODE"], poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)


def validate_qemu_image_format(dictImage, expected_format='qcow2'):
    poolname = dictImage.get('poolname', None)
    imagename = dictImage.get('imagename', None)
    cmd = "ssh %s qemu-image info rbd:%s/%s | sed -n '2p'" %\
          (os.environ["CLIENTNODE"], poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    actual_format = stdout.split(':')[-1].strip()
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
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
