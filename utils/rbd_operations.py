from launch import launch
import logging
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

def resizeRBDImage(dictImg):
    name = dictImg.get('name', None)
    size = dictImg.get('size', 1250)
    pool = dictImg.get('pool', 'rbd')
    cmd = "ssh %s rbd -p %s resize --image=%s --size=%s" %(os.environ["CLIENTNODE"], pool, name, size)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

def rbdGetPoolImages(poolname):
    cmd = "ssh %s rbd -p %s ls" % (os.environ["CLIENTNODE"], poolname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    return stdout.strip().split('\n')

def validate_image_size(dictImage):
    poolname = dictImage.get('poolname', None)
    imagename = dictImage.get('imagename', None)
    size = dictImage.get('size_mb', None)
    cmd = "ssh %s rbd -p %s --image %s info"  % (os.environ["CLIENTNODE"], poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    new_size = "ssh %s rbd -p %s --image %s info | sed -n '2p'" % (os.environ["CLIENTNODE"], poolname, imagename)
    act_size_in_mb = new_size.split(' ')[1]
    # rewrite it with json output
    assert(str(size) in str(act_size_in_mb)), "new size for image %s was %s" % (imagename, new_size)
    log.info("validated image - %s in pool %s " % (imagename, poolname))


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
    return stdout.strip().split('\n')


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
    return stdout


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
    for snap in cmd:
        # only if snap is present # check python docs
        all_snaps.append(snap['name'])
    if expected_presence:
        assert (snapname in all_snaps), "Error the snapshot %s you supposed to have is not present" % (snapname)
    else:
        assert (snapname not in all_snaps), "Error the snapshot %s you supposed to have is not present" % (snapname)

def validate_snapshot_diff(dictSnapshot, expected_difference=False):
    poolname = dictSnapshot.get('poolname', None)
    snapname = dictSnapshot.get('snapname', None)
    imagename = dictSnapshot.get('imagename', None)
    cmd = "ssh %s rbd -p %s snap ls %s --format -json" %(os.environ["CLIENTNODE"], poolname, imagename)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    diff = "ssh %s rbd -p %s diff %s --from-snap %s --format json" % (os.environ["CLIENTNODE"], poolname, imagename, poolname)
    if expected_difference:
        assert (diff != []), "Error. No differences between image: %s and snapshot: %s" % (imagename, snapname)
    else:
        assert (diff == []), "Error. Differences between image: %s and snapshot: %s" % (imagename, snapname)


def copy, move.. etc

def lock_snapshot(dictSnapshot):
    pass


def unprotect_snapshot(dictSnapshot):
    pass


def protect_snapshot(dictSnapshot):
    pass


def clone_snapshot(dictSnapshot):
    pass

# DIFF!






