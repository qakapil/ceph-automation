import rados
import rbd
import logging

log = logging.getLogger(__name__)

cluster = rados.Rados(conffile='/etc/ceph/ceph.conf')
cluster.connect()
print('created the cluster object')

pool_ctx = cluster.open_ioctx('rbd')
print('created the pool ctx for rbd pool')

rbd_inst = rbd.RBD()
size = 0.3*1024**3
size = int(size)
print('creating image test_librbdImg of size '+str(size))
rbd_inst.create(pool_ctx, 'test_librbdImg', size)
print('created image test_librbdImg of size '+str(size))

image_ctx = rbd.Image(pool_ctx, 'test_librbdImg')
print('created the image ctx for test_librbdImg')

rbd_inst = rbd.RBD()
imglist = rbd_inst.list(pool_ctx)
assert('test_librbdImg' in imglist),"test_librbdImg could \
            was not created"

size_bytes = image_ctx.size()
print('image size is - '+str(size_bytes) +' and datatype is'+str(type(size_bytes)))

expsize = 0.3*1024**3
size = str(int(size)).strip()
expsize = str(int(expsize)).strip()
print('actual image size is '+size)
print('expected image size is '+expsize)
assert(size == expsize),"image size not as expected"

image_ctx.close()
rbd_inst.remove(pool_ctx, 'test_librbdImg')
pool_ctx.close()
cluster.shutdown()