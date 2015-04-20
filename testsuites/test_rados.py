from utils import monitoring
from utils import operations
from utils import baseconfig
from utils import rados_operations
from utils import general

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


def test_pools():
    global vErrors
    try:
        pool_name = 'test_pool'
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        if pool_name in pool_list:
            rados_operations.rmpool(pool_name)
        rados_operations.mkpool(pool_name)
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        assert (pool_name in pool_list), "newly created pool was not found in lspools ouput"
        rados_operations.rmpool(pool_name)
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        assert (pool_name not in pool_list), "pool %s could not be deleted. pool list is %s" % (pool_name, str(pool_list))
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log.error(str(exc_type)+" : "+str(exc_value)+" : "+str(exc_traceback))
        sError = str(sys.exc_info()[0])+" : "+str(sys.exc_info()[1])
        log.error(inspect.stack()[0][3] + "Failed with error - "+sError)
        vErrors.append(sError)
        raise Exception(str(sys.exc_info()[1]))


def test_copypool():
    global vErrors
    try:
        pool_name1 = 'test_pool1'
        pool_name2 = 'test_pool2'
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        if pool_name1 in pool_list:
            rados_operations.rmpool(pool_name2)
        rados_operations.mkpool(pool_name1)
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        assert (pool_name1 in pool_list), "newly created pool was not found in lspools ouput"
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        if pool_name2 in pool_list:
            rados_operations.rmpool(pool_name2)
        rados_operations.mkpool(pool_name2)
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        assert (pool_name2 in pool_list), "newly created pool was not found in lspools ouput "

        obj_name = 'test_object'
        rados_operations.create_object(obj_name, pool_name1)
        pool1_objects = rados_operations.rados_ls(pool_name1)
        pool1_objects = pool1_objects.split('\n')
        assert (obj_name in pool1_objects), "object was not created"
        rados_operations.cppool(pool_name1, pool_name2)
        pool2_objects = rados_operations.rados_ls(pool_name2)
        pool2_objects = pool2_objects.split('\n')
        assert (pool1_objects == pool2_objects), "objects in the two lists were not same"

        rados_operations.rmpool(pool_name1)
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        assert (pool_name1 not in pool_list), "pool %s could not be deleted. pool list is %s" % (pool_name1, str(pool_list))
        rados_operations.rmpool(pool_name2)
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        assert (pool_name2 not in pool_list), "pool %s could not be deleted. pool list is %s" % (pool_name2, str(pool_list))
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log.error(str(exc_type)+" : "+str(exc_value)+" : "+str(exc_traceback))
        sError = str(sys.exc_info()[0])+" : "+str(sys.exc_info()[1])
        vErrors.append(sError)
        raise Exception(str(sys.exc_info()[1]))


def test_objects():
    try:
        pool_name = 'test_pool'
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        if pool_name in pool_list:
            rados_operations.rmpool(pool_name)
        rados_operations.mkpool(pool_name)
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        assert pool_name in pool_list, "newly created pool was not found in lspools ouput"
        filename = 'test_file.txt'
        cmd = "ssh %s touch %s" % (os.environ["CLIENTNODE"], filename)
        general.eval_returns(cmd)
        obj_name = 'test_obj'
        rados_operations.put_object('test_obj', filename, pool_name)
        pool_objects = rados_operations.rados_ls(pool_name)
        pool_objects = pool_objects.split('\n')
        assert (obj_name in pool_objects), "object was not created "
        cp_obj_name = 'test_obj_copy'
        rados_operations.copy_object(obj_name, cp_obj_name, pool_name)
        obj_stat = rados_operations.stat_object(obj_name, pool_name)
        obj_size = obj_stat.split(",")[1].strip()
        obj_cp_stat = rados_operations.stat_object(cp_obj_name, pool_name)
        obj_cp_size = obj_cp_stat.split(",")[1].strip()
        assert (obj_size == obj_cp_size), "copied objets size was not same"
        rados_operations.rmpool(pool_name)
        pool_list = rados_operations.lspools()
        pool_list = pool_list.split('\n')
        assert (pool_name not in pool_list), "pool %s could not be deleted. pool list is %s" % (pool_name, str(pool_list))
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log.error(str(exc_type)+" : "+str(exc_value)+" : "+str(exc_traceback))
        sError = str(sys.exc_info()[0])+" : "+str(sys.exc_info()[1])
        vErrors.append(sError)
        raise Exception(str(sys.exc_info()[1]))


def teardown_module():
    log.info('++++++completed rbd test suite ++++++')
    if vErrors:
        log.info('test suite failed with these errors - '+str(vErrors))
    else:
        log.info('starting teardown in teardown_module')
        general.perNodeCleanUp(yaml_data['allnodes'], 'ceph')
