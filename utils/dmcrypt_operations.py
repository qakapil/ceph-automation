from launch import launch
import logging
import general
import os, time
import monitoring
from utils import zypperutils
from utils import cephdeploy

log = logging.getLogger(__name__)


def get_partition_for_disk():
    cmd = "ssh %s fdisk -l /dev/vdb | grep '^/dev' | cut -d' ' -f1" % (os.environ["CLIENTNODE"])
    stdout, stderr = general.eval_returns(cmd)
    return stdout.split("\n")


def validate_partition_type():
    cmd = "ssh %s blkid -o value -s TYPE" % (os.environ["CLIENTNODE"])
    stdout, stderr = general.eval_returns(cmd)
    types = stdout.split("\n")
    return True if 'crypto_LUKS' in types else False


def validate_is_mapper(partition=None):
    # PART_UUID is of partition should be /dev/mapper/PART_UUID
    assert (partition != None), "Error, partition not provided"
    cmd = "ssh %s blkid - s PARTUUID - d %s -o value" % (os.environ["CLIENTNODE"], partition)
    stdout, stderr = general.eval_returns(cmd)
    return stdout


def device_exists(partuuid=None):
    assert (partuuid != None), "Error, partuuid not provided"
    cmd = "ssh %s ls /dev/mapper/%s" % (os.environ["CLIENTNODE"], partuuid)
    stdout, stderr = general.eval_returns(cmd)
    return True if stdout is not None else False


def validate_dmcrypt_key(partuuid=None):
    assert (partuuid != None), "Error, partuuid not provided"


# confirm systemd ceph-disk-activate // activate-journal are up
# validate TYPE == crypto_luks (crypto)
# validate /dev/mapper
# validate if its plain or luks
# validate if key_server is used

