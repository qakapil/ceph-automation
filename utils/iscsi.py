import logging
import general
from launch import launch
import socket
import sys
import os
import json
import jsontree
from collections import OrderedDict
import xmlrpclib
from xml.dom.minidom import parse, parseString, Node


log = logging.getLogger(__name__)


def targetService(node, action):
    status = {'start': 'Active: active', 'restart': 'Active: active', 'stop': 'Active: inactive'}
    cmd = 'ssh %s sudo systemctl %s target' % (node, action)
    stdout, strderr = general.eval_returns(cmd)
    cmd = 'ssh %s sudo systemctl status target' % node
    stdout, strderr = general.eval_returns(cmd)
    assert (status[action] in stdout.strip()), "error with target service on node %s" % node


def addBlock(node, block_name, drive_name):
    cmd = 'ssh %s sudo tcm_node --block %s %s' % (node, block_name, drive_name)
    general.eval_returns(cmd)
    cmd = 'ssh %s sudo tcm_node --listhbas %s' % (node, block_name)
    stdout, strderr = general.eval_returns(cmd)
    assert (drive_name in stdout.strip()), "error with iBlock creation on node %s" % node


def addIQNTPG(node, iqn, tpg):
    cmd = 'ssh %s sudo lio_node --listtargetnames' % node
    stdout, strderr = general.eval_returns(cmd)
    targets_list = stdout.split('\n')
    targets_list = map(str.strip, targets_list)
    if iqn in targets_list:
        cmd = 'ssh %s sudo lio_node --listtpgparam %s %s' % (node, iqn, tpg)
        rc, stdout, stderr = launch(cmd=cmd)
        assert (rc != 0), "%s with %s already exist on node %s" % (iqn, tpg, node)
    cmd = 'ssh %s sudo lio_node --addtpg %s %s' % (node, iqn, tpg)
    general.eval_returns(cmd)
    cmd = 'ssh %s sudo lio_node --listtargetnames' % node
    stdout, strderr = general.eval_returns(cmd)
    targets_list = stdout.split('\n')
    targets_list = map(str.strip, targets_list)
    assert (iqn in targets_list), "iqn %s was not created on node %s" % (iqn, node)
    cmd = 'ssh %s sudo lio_node --listtpgparam %s %s' % (node, iqn, tpg)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "tpg %s was not created for iqn %s on node %s" % (tpg, iqn, node)
    

def addNP(node, iqn, tpg, ip, port):
    cmd = 'ssh %s sudo lio_node --addnp %s %s %s:%s' % (node, iqn, tpg, ip, port)
    general.eval_returns(cmd)
    cmd = 'ssh %s sudo lio_node --listnps %s %s' % (node, iqn, tpg)
    stdout, strderr = general.eval_returns(cmd)
    ip_port = '%s:%s' % (ip, port)
    assert (ip_port == stdout.strip()), "NP %s could not be added" % ip_port


def disableAuth(node, iqn, tpg):
    cmd = 'ssh %s sudo lio_node --disableauth %s %s' % (node, iqn, tpg)
    general.eval_returns(cmd)


def enableDemoMode(node, iqn, tpg):
    cmd = 'ssh %s sudo lio_node --demomode %s %s' % (node, iqn, tpg)
    general.eval_returns(cmd)


def enableTPG(node, iqn, tpg):
    cmd = 'ssh %s sudo lio_node --enabletpg %s %s' % (node, iqn, tpg)
    general.eval_returns(cmd)


def addLun(node, iqn, tpg, lun_num, lun_name, block_name):
    cmd = 'ssh %s sudo lio_node --addlun %s %s %s %s %s' % (node, iqn, tpg, lun_num, lun_name, block_name)
    general.eval_returns(cmd)
    lun_dir = '/sys/kernel/config/target/iscsi/%s/tpgt_%s/lun/lun_%s/%s' % (iqn, tpg, lun_num, lun_name)
    cmd = 'ssh %s ls %s' % (node, lun_dir)
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "lun %s was not added for block %s" % (lun_name, block_name)


def demoModeWriteProtect(node, iqn, tpg):
    file_path = '/sys/kernel/config/target/iscsi/%s/tpgt_%s/attrib/demo_mode_write_protect' % (iqn, tpg)
    cmd = '''ssh %s "sudo sh -c 'echo 0 >> %s'"''' % (node, file_path)
    general.eval_returns(cmd)
    cmd = 'ssh %s cat %s' % (node, file_path)
    stdout, strderr = general.eval_returns(cmd)
    assert (str(stdout.strip()) == '0'), "demo mode write protect was not set on node %s" % node


def discoverLoginTarget(client_node, target_node, iqn, tpg, port):
    target_node_ip = socket.gethostbyname(target_node)
    cmd = 'ssh %s sudo iscsiadm -m discovery -p %s:%s -t sendtargets' % (client_node, target_node_ip, port)
    stdout, strderr =  general.eval_returns(cmd)
    assert(len(stdout.strip().split('\n')) == 1), "more than one target found on %s for port %s" % (target_node_ip, port)

    target = stdout.split('\n')[0].strip()

    exp_target = '%s:%s,%s %s' % (target_node_ip, port, tpg, iqn)
    assert (target == exp_target), "actual target %s did not match expected %s" % (target, exp_target)
    
    cmd = "ssh %s lsblk -io KNAME,TYPE,SIZE,MODEL | grep IBLOCK | awk '{print $1}'" % client_node
    stdout, strderr = general.eval_returns(cmd)
    curr_iblocks = stdout.split('/n')
   
    cmd = 'ssh %s sudo iscsiadm -m node -T %s -p %s:%s --login' % (client_node, iqn, target_node_ip, port)
    stdout, strderr = general.eval_returns(cmd)
    
    validate_string = "Login to [iface: default, target: %s, portal: %s,%s] successful" % (iqn, target_node_ip, port)
    assert (validate_string in stdout), "could not login to target with iqn %s" % iqn

    cmd = "ssh %s lsblk -io KNAME,TYPE,SIZE,MODEL | grep IBLOCK | awk '{print $1}'" % client_node
    stdout, strderr = general.eval_returns(cmd)
    new_iblocks = stdout.split('/n')

    created_blocks = list(set(new_iblocks) - set(curr_iblocks))
    assert (len(created_blocks) == 1), "length of target created was not one"
   
    return created_blocks[0].strip()


def partitionIBlock(node, block):
    cmd = "ssh %s lsblk -io KNAME,TYPE,SIZE,MODEL | awk '{print $1}' | grep %s" % (node, block)
    stdout, strderr =  general.eval_returns(cmd)
    drives = stdout.strip().split('\n')
    assert (len(drives) == 1), "the block %s was either not found or already partitioned - %s" % (block, drives)

    cmd = '''ssh %s "echo -e 'o\\nn\\np\\n1\\n\\n\\nw' | sudo fdisk /dev/%s"''' % (node, block)
    general.eval_returns(cmd)
   
    cmd = "ssh %s lsblk -io KNAME,TYPE,SIZE,MODEL | awk '{print $1}' | grep %s1" % (node, block)
    stdout, strderr =  general.eval_returns(cmd)
    drives = stdout.strip().split('\n')
    assert (len(drives) == 1), "the block %s was not partitioned- %s" % (block, drives)
  
    return drives[0].strip()


def createFSMount(node, drive, fs, test_dir):
    cmd = 'ssh %s sudo mkfs.%s /dev/%s' % (node, fs, drive)
    general.eval_returns(cmd)
    cmd = 'ssh %s rm -rf %s' % (node, test_dir)
    general.eval_returns(cmd)
    cmd = 'ssh %s mkdir %s' % (node, test_dir)
    general.eval_returns(cmd) 
    cmd = 'ssh %s sudo mount /dev/%s %s' % (node, drive, test_dir)
    general.eval_returns(cmd)
    cmd = 'ssh %s sudo chown jenkins:users %s' % (node, test_dir)
    general.eval_returns(cmd)


def cleanupISCSI(client_node, target_node, iqn, port, block_name, drive_name):
    target_node_ip = socket.gethostbyname(target_node)

    cmd = 'ssh %s sudo iscsiadm -m node -T %s -p %s:%s --logout' % (client_node, iqn, target_node_ip, port)
    stdout, strderr = general.eval_returns(cmd)

    validate_string = "target: %s, portal: %s,%s] successful" % (iqn, target_node_ip, port)
    assert (validate_string in stdout), "could not login to target with iqn %s" % iqn

    cmd = 'ssh %s sudo lio_node --deliqn %s' % (target_node, iqn)
    general.eval_returns(cmd)

    cmd = 'ssh %s sudo tcm_node --freedev %s' % (target_node, block_name)
    general.eval_returns(cmd)

    cmd = 'ssh %s sudo rbd unmap %s' % (target_node, drive_name)
    general.eval_returns(cmd)

    cmd = "ssh %s lsblk -io KNAME,TYPE,SIZE,MODEL | grep IBLOCK | awk '{print $1}'" % (target_node)
    stdout, strderr = general.eval_returns(cmd)
    iblocks = stdout.strip().split('\n')
    for iblock in iblocks:
        if iblock != '':
            cmd = 'ssh %s sudo umount /dev/%s1' % (target_node, iblock)
            general.eval_returns(cmd)


def iscsiService(node, action):
    status = {'start': 'Active: active', 'restart': 'Active: active', 'stop': 'Active: inactive'}
    cmd = 'ssh %s sudo systemctl %s iscsi' % (node, action)
    stdout, strderr = general.eval_returns(cmd)
    cmd = 'ssh %s sudo systemctl status iscsi' % node
    stdout, strderr = general.eval_returns(cmd)
    assert (status[action] in stdout.strip()), "error with target service on node %s" % node


def addMultiPathNIC(node, nic, ip_addr, gw_addr, ifcfg_template_file):
    #ip = socket.gethostbyname(node)
    ifcfg_p1 = ifcfg_template_file % ('static', ip_addr)
    ifcfg_filename = 'ifcfg-'+nic+'-mp1'
    ifcfg_nic_id = 'ifcfg-'+nic
    file_writer = open(ifcfg_filename, "w")

    file_writer.write(ifcfg_p1)
    file_writer.close()

    #-- Is the nic passed available on the server in question.
    cmd = "ssh root@%s 'ip link ls dev %s | grep -i %s | cut -d\: -f2 | tr -d '[[:space:]]''"  % (node, nic, nic)
    rc, stdout, stderr = launch(cmd=cmd)
    if stdout != nic:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'. Network Interface %s does not exist." % (cmd, stderr, nic)

    cmd = 'scp %s root@%s:/etc/sysconfig/network/%s' % (ifcfg_filename, node, ifcfg_nic_id)
    #general.eval_returns(cmd)
    rc, stdout, stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)

    cmd = "ssh root@%s 'ifdown %s && sleep 5 && ifup %s && sleep 10 && route add default gw %s %s'"\
          % (node, nic, nic, gw_addr, nic)

    rc, stdout, stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)


def discoverMultiPathLoginTarget(client_node, target_node, iqn, tpg, port):
    target_node_ip = socket.gethostbyname(target_node)
    cmd = 'ssh %s sudo iscsiadm -m discoverydb -t st -p %s:%s --discover' % (client_node, target_node_ip, port)
    stdout, strderr =  general.eval_returns(cmd)
    assert(len(stdout.strip().split('\n')) >= 1), "No target(s) found on %s for port %s" % (target_node_ip, port)

    target = stdout.split('\n')[0].strip()

    exp_target = '%s:%s,%s %s' % (target_node_ip, port, tpg, iqn)
    assert (target == exp_target), "actual target %s did not match expected %s" % (target, exp_target)

    cmd = "ssh %s lsblk -io KNAME,TYPE,SIZE,MODEL | grep IBLOCK | awk '{print $1}'" % client_node
    stdout, strderr = general.eval_returns(cmd)
    curr_iblocks = stdout.split('/n')

    cmd = 'ssh %s sudo iscsiadm -m node -l' % client_node
    stdout, strderr = general.eval_returns(cmd)

    validate_string = "Login to [iface: default, target: %s, portal: %s,%s] successful" % (iqn, target_node_ip, port)
    assert (validate_string in stdout), "could not login to target with iqn %s" % iqn

    cmd = "ssh %s lsblk -io KNAME,TYPE,SIZE,MODEL | grep IBLOCK | awk '{print $1}'" % client_node
    stdout, strderr = general.eval_returns(cmd)
    new_iblocks = stdout.split('/n')

    created_blocks = list(set(new_iblocks) - set(curr_iblocks))
    assert (len(created_blocks) >= 1), "length of target(s) created was not one or more"
    return created_blocks[0].strip()


def listIPAddresses(node):
    #-- All ip addresses, except ipv6 and localhost related addrs.
    cmd = "ssh %s sudo ifconfig | grep -i 'inet' | grep -iv '127.' | grep -iv 'inet6' | awk {'print $2'} | sed -ne 's/addr\:/ /p'" % node
    stdout, strderr =  general.eval_returns(cmd)
    addrList =  stdout.strip().split('\n')

    assert(len(addrList) >= 1), "No IP addresses listed on %s" % (node)
    return addrList


def listNICsAndIPs(node):
    tmpShellScript = "/tmp/getallnetinfo.sh"
    tmpShellScriptCmd= """ip addr | awk '/^[0-9]+:/ {sub(/:/,"",$2); iface=$2} /^[[:space:]]*inet /{
    split($2, a, "/")
    print iface":"a[1] }'
    """
    fileOutTmp = open(tmpShellScript, "w")
    fileOutTmp.writelines(tmpShellScriptCmd)
    fileOutTmp.close()
    cmd = 'scp %s root@%s:%s' % (tmpShellScript, node, tmpShellScript)
    #general.eval_returns(cmd)
    rc, stdout, stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)

    cmd = "ssh %s sudo bash %s" % (node, tmpShellScript)
    stdout, strderr =  general.eval_returns(cmd)
    nicIPList =  stdout.strip().split('\n')
    #-- Check and delete tmp file.
    if os.path.isfile(tmpShellScript):
        try:
            os.remove(tmpShellScript)
        except OSError, exc:
            log.info("Error trying to delete tmp script file %s. %s " % (tmpShellScript, exc.strerror))
    else:
        log.info("Temp script file %s was not found in place to be deleted" % (tmpShellScript))

    return nicIPList


def dictNICsAndIPs(node):
    nicIPList = listNICsAndIPs(node)

    #-- Spliting properly the list and checking it into a directory.
    dictNicIP={}
    for nicIP in nicIPList:
        nicIP = nicIP.strip()
        #-- We don't care about loopback addresses.
        if nicIP and ('lo:127.' not in nicIP):
            iface, iaddr = nicIP.split(":", 1)
            dictNicIP [iface] = iaddr

    return dictNicIP


def disableIFace(node, iface):
    cmd = "ssh root@%s 'ifdown %s '" % (node, iface)

    rc, stdout, stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)


def enableIFace(node, iface):
    cmd = "ssh root@%s 'ifup %s && sleep 10'" % (node, iface)

    rc, stdout, stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)


def updateRoutes(node, iface, gw_addr):
    cmd = "ssh root@%s 'route add default gw %s %s'" % (node, gw_addr, iface)

    rc, stdout, stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)


def addMultiPathNP(node, iqn, tpg, ipList, port):
    #-- Loop thru all addresses and addnp them.
    for ipAddr in ipList:
        ipAddr = ipAddr.strip()
        if ipAddr:
            cmd = 'ssh %s sudo lio_node --addnp %s %s %s:%s' % (node, iqn, tpg, ipAddr, port)
            general.eval_returns(cmd)
            cmd = 'ssh %s sudo lio_node --listnps %s %s' % (node, iqn, tpg)
            stdout, strderr = general.eval_returns(cmd)
            ip_port = '%s:%s' % (ipAddr, port)
            assert (ip_port in stdout.strip()), "NP %s could not be added" % ip_port


def createMultiPathFSMount(node, drive, fs, test_dir):
    cmd = 'ssh %s sudo mkfs.%s /dev/%s' % (node, fs, drive)
    rc, stdout, stderr = launch(cmd=cmd)

    #-- rdb was mounted and mapped thru /dev/%drive, and needs to be accessed via
    #-- device mapper id. Used by multipath.
    mountingPoint = ('/dev/%s' % drive)
    validate_string = 'cannot open /dev/%s: Device or resource busy' % drive
    if validate_string in stderr:
        if isDMusedOnBlock(node, drive):
            cmd = "ssh %s udevadm info /dev/%s | grep -i 'ID_SERIAL=' | cut -d\: -f2 | cut -d= -f2 | tr -d '[[:space:]]'" % (node, drive)
            stdout, strderr =  general.eval_returns(cmd)
            devMap = stdout.strip()
            assert devMap
            cmd = "ssh %s parted -s '/dev/mapper/%s unit cyl print unit s print'" % (node, devMap)
            stdout, strderr =  general.eval_returns(cmd)
            invalid_string = "Could not stat device /dev/mapper/%s" % devMap
            assert (invalid_string not in strderr)
            cmd = "ssh %s udevadm info /dev/mapper/%s-part1 | grep -i 'DM_NAME=' | cut -d\: -f2 | cut -d= -f2 | tr -d '[[:space:]]'" % (node, devMap)
            stdout, strderr =  general.eval_returns(cmd)
            partMap = stdout.strip()
            invalid_string = "Unknown device"
            assert (invalid_string not in strderr)
            cmd = "ssh %s udevadm info /dev/mapper/%s | grep -i 'DEVNAME=' | cut -d\: -f2 | cut -d= -f2 | tr -d '[[:space:]]'" % (node, partMap)
            stdout, strderr =  general.eval_returns(cmd)
            dmMap = stdout.strip()
            assert dmMap
            cmd = "ssh %s udevadm info /dev/mapper/%s | grep -i 'ID_PART_ENTRY_UUID=' | cut -d\: -f2 | cut -d= -f2 | tr -d '[[:space:]]'" % (node, partMap)
            stdout, strderr =  general.eval_returns(cmd)
            euuidMap = stdout.strip()
            assert euuidMap
            #--
            assert fs == 'xfs' or fs == 'btrfs'
            if fs == 'xfs':
                cmd = "ssh %s sudo mkfs.%s -q -f -m crc=1 '/dev/mapper/%s'" % (node, fs, partMap)
            elif fs == 'btrfs':
                cmd = "ssh %s sudo mkfs.%s -f '/dev/mapper/%s'" % (node, fs, partMap)

            general.eval_returns(cmd)
            mountingPoint = ('/dev/mapper/%s' % partMap)

    cmd = 'ssh %s rm -rf %s' % (node, test_dir)
    general.eval_returns(cmd)
    cmd = 'ssh %s mkdir %s' % (node, test_dir)
    general.eval_returns(cmd)
    cmd = 'ssh %s sudo mount -t %s %s %s' % (node, fs, mountingPoint, test_dir)
    general.eval_returns(cmd)
    cmd = 'ssh %s sudo chown jenkins:users %s' % (node, test_dir)
    general.eval_returns(cmd)


def generateDDFiles(node, location):
    cmd = "ssh %s dd if='/dev/zero' of='%s/mp-test1.dd' bs=32k count=1k seek=1000000 conv=fdatasync" % (node, location)
    stdout, strderr =  general.eval_returns(cmd)
    cmd = "ssh %s dd if='/dev/zero' of='%s/mp-test2.dd' bs=1M count=512 conv=fdatasync" % (node, location)
    stdout, strderr =  general.eval_returns(cmd)
    cmd = "ssh %s ls -l %s/*.dd | wc -l" % (node, location)
    stdout, strderr =  general.eval_returns(cmd)
    filesCreated = stdout.strip()
    assert (filesCreated >= 2), "We should have a minimum of 2 files (*.dd) created on node %s at %s" % (node, location)


def isDMused(node):
    cmd = 'ssh %s dmsetup ls' % node
    stdout, strderr =  general.eval_returns(cmd)
    validate_string = "No devices found"
    if not (validate_string in stdout):
        result = True
    else:
        result = False
    return result


def isDMusedOnBlock(node, device):
    cmd = "ssh %s /sbin/udevadm info /dev/%s | grep -i 'DM_MULTIPATH_DEVICE_PATH' | cut -d\: -f2 | tr -d '[[:space:]]'" % (node, device)
    stdout, strderr =  general.eval_returns(cmd)
    dmMultiPath = stdout.strip()
    result = False
    if dmMultiPath == 'DM_MULTIPATH_DEVICE_PATH=1':
        result = True
    return result


def addInitiatorToTargetACL(target_node, target_iqn, tpgt, initiator_iqn, client_lun, target_lun):
    cmd = 'ssh %s sudo lio_node --addlunacl %s %s %s %s %s' % (target_node, target_iqn, tpgt, initiator_iqn, client_lun, target_lun)
    stdout, stderr = general.eval_returns(cmd)
    stdout.strip()
    if stdout:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'. ACL was not added." % (cmd, stderr)


def runDiscoveryOnInitiator(initiator_node, target_addr, target_port, target_iqn):
    cmd = 'ssh %s sudo iscsiadm -m discoverydb -t st -p %s:%s --discover' % (initiator_node, target_addr, target_port)
    stdout, stderr = general.eval_returns(cmd)
    discoveryList =  stdout.strip().split('\n')
    assert(len(discoveryList) > 1), "Only one path to target found on %s port %s" % (target_addr, target_port)
    #-- "192.168.110.21:3260,1 iqn.2015-08.de.suse:01:92f9821dd121"
    assert_string = " %s" % (target_iqn)
    if not (assert_string in stdout):
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'. " % (cmd, stderr)
    return discoveryList


def initiatorLoginAllTargets(initiator_node, targetsList):
    cmd = 'ssh %s sudo iscsiadm -m node -u' % initiator_node
    rc, stdout, stderr = launch(cmd=cmd)
    cmd = 'ssh %s sudo iscsiadm -m node -l' % initiator_node
    stdout, strderr = general.eval_returns(cmd)
    for target in targetsList:
        target = target.strip()
        if target:
            #log.info("target: (%s)" % (target))
            targetstr = str(target)
            targetIP_Port, targetIQN = targetstr.split(" ", 1)
            targetIP_Port = targetIP_Port.rpartition(",")[0]
            targetIP_Port = targetIP_Port.replace(":", ",")
            validate_string = "Login to [iface: default, target: %s, portal: %s] successful" % (targetIQN, targetIP_Port)
            assert (validate_string in stdout), "could not login to target address: [%s], iqn: [%s]" % (targetIP_Port, targetIQN)


def multipathService(node, action):
    status = {'start': 'Active: active', 'restart': 'Active: active', 'stop': 'Active: inactive'}
    cmd = 'ssh %s sudo systemctl %s multipathd' % (node, action)
    stdout, strderr = general.eval_returns(cmd)
    cmd = 'ssh %s sudo systemctl status multipathd' % node
    stdout, strderr = general.eval_returns(cmd)
    assert (status[action] in stdout.strip()), "error with multipathd service on node %s" % node


def listMultiPaths(initiator_node):
    cmd = 'ssh %s sudo lsscsi' % (initiator_node)
    stdout, strderr = general.eval_returns(cmd)
    cmd = 'ssh %s sudo multipath -ll' % (initiator_node)
    stdout, strderr = general.eval_returns(cmd)


def mountingPointOnInitiator(initiator_node, mounting_point, fs_type, target_node):
    targetNodeBlock = findBlockOnNode(target_node)
    assert targetNodeBlock
    targetDMSerial = findBlockSNOnNode(target_node, targetNodeBlock)
    assert targetDMSerial
    multiPathLocation = ('/dev/mapper/%s-part1' % targetDMSerial)

    if isMountingPointActive(initiator_node, mounting_point):
        cmd = 'ssh %s sudo umount %s' % (initiator_node, mounting_point)
        general.eval_returns(cmd)
        cmd = 'ssh %s sudo rm -rf %s/*' % (initiator_node, mounting_point)

    cmd = 'ssh %s mkdir -p %s' % (initiator_node, mounting_point)
    general.eval_returns(cmd)
    cmd = 'ssh %s sudo mount -t %s %s %s' % (initiator_node, fs_type, multiPathLocation, mounting_point)
    general.eval_returns(cmd)
    cmd = "ssh %s ls -l %s/*.dd | wc -l" % (initiator_node, mounting_point)
    stdout, strderr =  general.eval_returns(cmd)
    filesListed = stdout.strip()
    assert (filesListed >= 1), "We should have a minimum of 1 file (*.dd) created on node %s at %s, device: %s" % (initiator_node, mounting_point, targetDMSerial)

def listFilesOnMountingPoint(node, mounting_point):
    cmd = "ssh %s ls -l %s/*.dd | wc -l" % (node, mounting_point)
    stdout, strderr =  general.eval_returns(cmd)
    filesListed = stdout.strip()
    return filesListed


def isMountingPointActive(host_node,  mounting_point):
    cmd = "ssh %s sudo mount | grep -i '%s' | wc -l | tr -d '[[:space:]]'" % (host_node, mounting_point)
    stdout, strderr =  general.eval_returns(cmd)
    mountsFound =  int(stdout.strip())
    result = True if (mountsFound >= 1) else False
    return result


def findBlockOnNode(host_node):
    cmd = "ssh %s lsblk -io KNAME,TYPE,SIZE,MODEL | grep IBLOCK | awk '{print $1}'" % host_node
    stdout, strderr = general.eval_returns(cmd)
    new_iblocks = stdout.split('/n')
    created_blocks = list(set(new_iblocks))
    assert (len(created_blocks) >= 1), "length of target(s) created was not one or more"
    return created_blocks[0].strip()


def findBlockSNOnNode(host_node, drive):
    cmd = "ssh %s udevadm info /dev/%s | grep -i 'ID_SERIAL=' | cut -d\: -f2 | cut -d= -f2 | tr -d '[[:space:]]'" % (host_node, drive)
    stdout, strderr =  general.eval_returns(cmd)
    devMap = stdout.strip()
    assert devMap
    return devMap


def getListOfFilesOnDir(node, pathToDir):
    cmd = "ssh %s ls -1 %s/ | awk -F'/' '{print $NF}'" % (node, pathToDir)
    stdout, strderr =  general.eval_returns(cmd)
    filesListed = stdout.strip().split('\n')
    return filesListed

def readJSONFile(node, pathToFile):
    #jsonFile = open(pathToFile)
    #jsonData = json.load(jsonFile)
    #jsonFile.close()
    cmd = "ssh %s 'sudo cat %s'" % (node, pathToFile)
    stdout, strderr =  general.eval_returns(cmd)

    try:
        #jsonContent = json.dumps(jsonContent, sort_keys=True, indent=4)
        jsonContent = json.loads(stdout, object_pairs_hook=OrderedDict)
        jsonContent = json.dumps(jsonContent, indent=4)
        return jsonContent
    except (ValueError, KeyError, TypeError):
        log.info("JSON File %s/%s format error. " % (node, pathToFile))


#def replaceJSONRefs(jsonStruct, jKey, jValueCmp, jValueNew):
def replaceJSONRefs(jsonStruct, replList):
    jsonStructNew = jsonStruct    # (json.loads(jsonStruct)) will convert it to a data dict. We want string now.
    for key, value in replList.items():
        jsonStructNew = jsonStructNew.replace(key, value)

    '''
    # using data dict. #
    jsonStructNew = (json.loads(jsonStruct))    # jsonStruct     ##(json.loads(jsonFileData))
    for key, item in jsonStructNew.iteritems():  #.items(): Python 3x
        for data in item:
            for k, v in data.iteritems():  #   .items():
                if v == jValueCmp:
                    data[k] = jValueNew

    '''
    return jsonStructNew


def getJSONValues(jAttrib, jsonStruct):
    resultList=[]
    """
    def _read_dict(_dict):
        try:
            resultList.append(_dict[jAttrib])
        except KeyError:
            pass
        return _dict
    json.loads(jsonStruct, object_hook=_read_dict)
    #--
    jsonStructNew = (json.loads(jsonStruct))        #jsonStruct     ##(json.loads(jsonFileData))
    for key, value in jsonStructNew.iteritems():    #.items(): Python 3x
        log.info(" ->> key: (%s) / value: (%s)" % (key, value))
        for data in value:
            log.info("  -] data: (%s) /in value: (%s)" % (data, value))
            for k, v in data.iteritems():  #   .items():
                log.info("    -} k: (%s) / v: (%s)" % (k, v))
                #if v == jValueCmp:
                #    data[k] = jValueNew
    log.info("resultList: (%s) / jAttrib: (%s)" % (resultList, jAttrib))
    log.info("-----------------------------------------------------------")

    getPools = jsonStructNew['pools'][0]['pool']
    getGateways = jsonStructNew['pools'][0]['gateways']

    for gp in getPools:
        log.info(" ===>> gp: (%s)  /  getPools: (%s) " % (gp, getPools))

    for ggw in getGateways:
        log.info(" ===>> ggw: (%s)  /  getGateways: (%s) " % (ggw, getGateways))
        #log.info(" ===>> Testing...: (%s)  " % (ggw['host']))

    #-----------
    hosts = {}
    for pool in jsonStructNew['pools']:
        hosts[pool['pool']] = []
        log.info(" ==>> pools: (%s)  /  thePool: (%s) " % (jsonStructNew['pools'], pool))
        if 'gateways' in pool:
            for gateway in pool['gateways']:
                log.info("   ==>> gateways: (%s)  /  theGateway: (%s) " % (pool['gateways'], gateway))
                if 'host' in gateway:
                    hosts[pool['pool']].append(gateway['host'])
                    #log.info("     ==>> theHost: (%s) " % (pool[gateway['host']]))
                    #for host in pool[gateway['host']]:
                if 'target' in gateway:
                    hosts[pool['pool']].append(gateway['target'])
                    #log.info("     ==>> theTarget: (%s) " % (pool[gateway['target']]))

                #self._write_host(pool, gateway)
                #self._write_target(pool, gateway)
        #if 'auth' in jsonStruct:
            #self._write_auth(pool)
        #if 'targets' in jsonStruct:
            #self._write_targets(pool)
        #if 'portals' in jsonStruct:
            #self._write_portals(pool)
    #-----------
    """
    jsonStructNew = (json.loads(jsonStruct))

    """
    Build portal commands, assign address to correct TPG
    """
    #self.cmds = []
    #self.luns = []

    child_dict = {}
    for child in getChildren(jsonStructNew):
        if child not in child_dict:
            child_dict[child['pool']] = 'None'
            #if child[]

    #for jsonChunk in json.JSONEncoder.iterencode(jsonStruct):
    #    log.info(" -->> jsonChunk: (%s)  " % (jsonChunk))

    #if 'portals' in jsonStructNew:   # ['portals']:
    #    log.info(" -->> Thru portals: (%s)  " % (jsonStructNew['portals']))
    #    for target in jsonStructNew['portals']:   # .keys():
    #        log.info(" -->> target: (%s)  " % (target))
    #        for image in jsonStructNew['portals'][target]:
    #            log.info(" -->> image: (%s) " % (image))
    #            for portal in jsonStructNew['portals'][target][image]:
    #                log.info(" -->> portal: (%s) " % (portal))
    #                for entry in jsonStructNew['portals']:
    #                    log.info(" -->> target: (%s)  /  image: (%s)  /  portal: (%s)  /  entry: (%s) " % (target, image, portal, entry))

        #for target, image, portal, entry in _PortalEntries(' ', jsonStructNew):
        #    log.info(" ==>> target: (%s)  /  image: (%s)  /  portal: (%s)  /  entry: (%s) " % (target, image, portal, entry))
        #    if entry['name'] == portal:
        #        for address in entry['addresses']:
        #            log.info("   ==>> address: (%s) " % (address))
        #            #self._cmd(target, Runtime.config['portals'][target][image][portal], address)
        #            #logging.debug("Adding address {} to tpg {} under target {}".format(address, Runtime.config['portals'][target][image][portal], target))
    ##else:
    ##    self._cmd(iqn({}), "1", "")
    log.info("     ==>> child_dict: (%s) " % child_dict)
    log.info("-----------------------------------------------------")
    exit(1)
    return resultList

def getChildren(node):
    stack = [node]
    while stack:
        node = stack.pop()
        stack.extend(node['gateways'][::-1])
        yield node


def _PortalEntries(jKey, jsonStruct):
    """
    Generator
    """
    for target in jsonStruct['portals'].keys():
        log.info(" -->> target: (%s)  " % (target))
        for image in jsonStruct['portals'][target]:
            log.info(" -->> image: (%s) " % (image))

            for portal in jsonStruct['portals'][target][image]:
                log.info(" -->> portal: (%s) " % (portal))
                #self._check(portal)
                for entry in jsonStruct['portals']:
                    log.info(" -->> target: (%s)  /  image: (%s)  /  portal: (%s)  /  entry: (%s) " % (target, image, portal, entry))
                    yield(target, image, portal, entry)

    """
        #--
        hosts = {}
        if ('pools' in self.current and self.current['pools']):
            for pool in self.current['pools']:
                hosts[pool['pool']] = []
                # Add current gateways
                if 'gateways' in pool:
                    for gateway in pool['gateways']:
                        if 'host' in gateway:
                            hosts[pool['pool']].append(gateway['host'])
                        if 'target' in gateway:
                            hosts[pool['pool']].append(gateway['target'])
            for pool in self.submitted['pools']:
                # Subtract submitted gateways, skip new entries
                if 'gateways' in pool:
                    for gateway in pool['gateways']:
                        if ('host' in gateway and
                            gateway['host'] in hosts[pool['pool']]):
                            hosts[pool['pool']].remove(gateway['host'])
                        if ('target' in gateway and
                            gateway['target'] in hosts[pool['pool']]):
                            hosts[pool['pool']].remove(gateway['target'])
                # Remove difference
                for host in hosts[pool['pool']]:
                    self.attr.remove(str(pool['pool']), str(host))
                    logging.debug("Removing host {} from pool {}".format(host, pool))
    """


#-- As JSON won't allow dfs, we convert it to a python object and send it over to an XML decoder ...
#-- so we can extract then a Node we want to search.
def getJSONValueList(jKey, jsonStruct):
    _XMLDom = parseString(xmlrpclib.dumps((json.loads(jsonStruct),)))

    def _value(_XMLNode):
        elem = _XMLNode.nextSibling
        while elem and elem.nodeType != elem.ELEMENT_NODE:
            elem = elem.nextSibling
        return elem.getElementsByTagName('string')[0].firstChild.nodeValue if elem else None

    _list = [_value(_xmlNode) for _xmlNode in _XMLDom.getElementsByTagName('name') if _xmlNode.firstChild.nodeValue in jKey]
    _list = list(set(_list))
    return _list


'''
def traverseXMLTree(XMLDoc, depth=0):
    tag = XMLDoc.tagName
    for childNode in XMLDoc.childNodes:
        if childNode.nodeType == childNode.TEXT_NODE:
            if XMLDoc.tagName == 'pool':
                log.info("xmltree: %s  /  data: %s " % (depth*'  ', childNode.data))
        if childNode.nodeType == xml.dom.Node.ELEMENT_NODE:
            traverseXMLTree(childNode, (depth+1))
'''


def dumpFileOnDir(node, pathToFile, buffToWrite):
    localDir  = pathToFile.rsplit("/", 1)[0]
    localFile = pathToFile.rsplit("/", 1)[1]
    '''
    cmd = 'ssh %s mkdir -p %s' % (node, localDir)
    general.eval_returns(cmd)
    cmd = "echo '%s' | ssh %s 'sudo cat >%s' " % (buffToWrite, node, pathToFile)
    rc,stdout,stderr = launch(cmd=cmd)
    '''
    tmpJSONFile = general.getTmpFile(node, "/tmp/.lrdbtmpjson")
    fileOutTmp = open(tmpJSONFile, "w")
    fileOutTmp.writelines(buffToWrite)
    fileOutTmp.close()

    cmd = 'ssh %s mkdir -p %s' % (node, localDir)
    general.eval_returns(cmd)
    cmd = 'scp %s root@%s:%s' % (tmpJSONFile, node, pathToFile)
    rc, stdout, stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)


