import logging
import general
import os
import time

log = logging.getLogger(__name__)


def mkpool(pool_name, auid=None, crush_rule=None):
    cmd = "ssh %s rados mkpool %s" % (os.environ["CLIENTNODE"], pool_name)
    if auid:
        cmd = "%s %s" % (cmd, auid)
    if crush_rule:
        cmd = "%s %s" % (cmd, crush_rule)
    general.eval_returns(cmd)


def rmpool(pool_name):
    cmd = "ssh %s rados rmpool %s %s --yes-i-really-really-mean-it" % (os.environ["CLIENTNODE"], pool_name, pool_name)
    stdout, stderr = general.eval_returns(cmd)
    time.sleep(3)
    if "successfully deleted pool" not in stdout.strip():
        log.error("KAPSERR"+stdout+" : "+stderr)
        raise Exception("could not delete pool "+pool_name)

def cppool(src_pool, dest_pool):
    cmd = "ssh %s rados cppool %s %s" % (os.environ["CLIENTNODE"], src_pool, dest_pool)
    general.eval_returns(cmd)


def lspools():
    cmd = "ssh %s rados lspools" % (os.environ["CLIENTNODE"])
    general.eval_returns(cmd)
    stdout, stderr = general.eval_returns(cmd)
    return stdout


def rados_df(pool_name=None):
    if pool_name:
        cmd = "ssh %s rados -p %s df" % (os.environ["CLIENTNODE"], pool_name)
    else:
        cmd = "ssh %s rados df" % (os.environ["CLIENTNODE"])
    stdout, stderr = general.eval_returns(cmd)
    return stdout


def rados_ls(pool_name):
    cmd = "ssh %s rados -p %s ls" % (os.environ["CLIENTNODE"], pool_name)
    stdout, stderr = general.eval_returns(cmd)
    return stdout


def get_object(object_name, outfile, pool_name):
    cmd = "ssh %s rados -p %s get %s %s" % (os.environ["CLIENTNODE"], pool_name, object_name, outfile)
    general.eval_returns(cmd)


def put_object(object_name, infile, pool_name):
    cmd = "ssh %s rados -p %s put %s %s" % (os.environ["CLIENTNODE"], pool_name, object_name, infile)
    general.eval_returns(cmd)


def create_object(object_name, pool_name):
    cmd = "ssh %s rados -p %s create %s" % (os.environ["CLIENTNODE"], pool_name, object_name)
    general.eval_returns(cmd)


def remove_object(object_name, pool_name):
    cmd = "ssh %s rados -p %s rm %s" % (os.environ["CLIENTNODE"], pool_name, object_name)
    general.eval_returns(cmd)


def copy_object(src_object, dest_object, pool_name):
    cmd = "ssh %s rados -p %s cp %s %s" % (os.environ["CLIENTNODE"], pool_name, src_object, dest_object)
    general.eval_returns(cmd)


def stat_object(object_name, pool_name):
    cmd = "ssh %s rados -p %s stat %s" % (os.environ["CLIENTNODE"], pool_name, object_name)
    stdout, stderr = general.eval_returns(cmd)
    return stdout


def rados_lssnap(pool_name):
    cmd = "ssh %s rados -p %s lssnap" % (os.environ["CLIENTNODE"], pool_name)
    stdout, stderr = general.eval_returns(cmd)
    return stdout


def mksnap(object_name, pool_name):
    cmd = "ssh %s rados -p %s mksnap %s" % (os.environ["CLIENTNODE"], pool_name, object_name)
    general.eval_returns(cmd)


def rmsnap(object_name, pool_name):
    cmd = "ssh %s rados -p %s rmsnap %s" % (os.environ["CLIENTNODE"], pool_name, object_name)
    general.eval_returns(cmd)


def listsnaps(object_name, pool_name):
    cmd = "ssh %s rados -p %s listsnaps %s" % (os.environ["CLIENTNODE"], pool_name, object_name)
    stdout, stderr = general.eval_returns(cmd)
    return stdout


def locklist(object_name, pool_name):
    cmd = "ssh %s rados -p %s lock list %s" % (os.environ["CLIENTNODE"], pool_name, object_name)
    stdout, stderr = general.eval_returns(cmd)
    return stdout


def lockget(object_name, pool_name, lock_name):
    cmd = "ssh %s rados -p %s lock get %s %s" % (os.environ["CLIENTNODE"], pool_name, object_name, lock_name)
    general.eval_returns(cmd)


def lockbreak(object_name, pool_name, lock_name, locker_name):
    cmd = "ssh %s rados -p %s lock break %s %s %s" % (os.environ["CLIENTNODE"], pool_name, object_name, lock_name, locker_name)
    general.eval_returns(cmd)


def lockinfo(object_name, pool_name, lock_name):
    cmd = "ssh %s rados -p %s lock info %s %s" % (os.environ["CLIENTNODE"], pool_name, object_name, lock_name)
    stdout, stderr = general.eval_returns(cmd)
    return stdout
