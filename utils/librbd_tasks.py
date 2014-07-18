import rados
import rbd
import logging
log = logging.getLogger(__name__)

def createCluster(cephconf):
    cluster = rados.Rados(conffile='/etc/ceph/ceph.conf')
    cluster.connect()
    log.debug('created the cluster object')
    return cluster

def createPoolIOctx(poolname,cluster):
    pool_ctx = cluster.open_ioctx(poolname)
    log.debug('created the pool ctx for %s'+poolname)
    return pool_ctx


def createImage(sizeGB,imgname,pool_ctx):
    imglist = getImagesList(pool_ctx)
    if imgname in imglist:
        removeImage(pool_ctx, imgname)
    rbd_inst = rbd.RBD()
    size = sizeGB * 1024**3
    size = int(size)
    log.debug('creating image '+imgname+' of size '+str(size))
    rbd_inst.create(pool_ctx, imgname, size)
    log.info('created image '+imgname+' of size '+str(size))


def createImgCtx(imgname,pool_ctx):
    image_ctx = rbd.Image(pool_ctx, imgname)
    log.debug('created the image ctx for image '+imgname)
    return image_ctx  
    
def getImagesList(pool_ctx):
    rbd_inst = rbd.RBD()
    imglist = rbd_inst.list(pool_ctx)
    return imglist


def removeImage(pool_ctx, imgname):
    rbd_inst = rbd.RBD()
    rbd_inst.remove(pool_ctx, imgname)
    
    
def renameImage(pool_ctx, srcname, destname):
    rbd_inst = rbd.RBD()
    rbd_inst.rename(pool_ctx, srcname, destname)


def getrbdVersion():
    rbd_inst = rbd.RBD()
    return rbd_inst.version()


def writeToImage(image_ctx):
    data = 'foo' * 200
    image_ctx.write(data, 0)


def getImageSize(image_ctx):
    size_bytes = image_ctx.size()
    log.info('image size is - '+str(size_bytes) +' and datatype is'+str(type(size_bytes)))
    return size_bytes


def getImageStat(image_ctx):
    dict_stat = image_ctx.stat()
    return  dict_stat


def close_all(cluster,pool_ctx,image_ctx):
    image_ctx.close()
    pool_ctx.close()
    cluster.shutdown()


