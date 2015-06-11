import logging
import general
from launch import launch
import socket



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

    cmd = '''ssh %s "echo -e 'o\\nn\\np\\n1\\n\\n\\nw' | fdisk /dev/%s"''' % (node, block)
    general.eval_returns(cmd)
   
    cmd = "ssh %s lsblk -io KNAME,TYPE,SIZE,MODEL | awk '{print $1}' | grep %s1" % (node, block)
    stdout, strderr =  general.eval_returns(cmd)
    drives = stdout.strip().split('\n')
    assert (len(drives) == 1), "the block %s was not partitioned- %s" % (block, drives)
  
    return drives[0].strip()


def createFSMount(node, drive, fs):
    cmd = 'ssh %s sudo mkfs.%s /dev/%s' % (node, fs, drive)
    general.eval_returns(cmd)
    cmd = 'ssh %s rm -rf ~/iscsi_test' % node
    general.eval_returns(cmd)
    cmd = 'ssh %s mkdir ~/iscsi_test' % (node)
    general.eval_returns(cmd) 
    cmd = 'ssh %s sudo mount /dev/%s ~/iscsi_test' % (node, drive)
    general.eval_returns(cmd)
    cmd = 'ssh %s sudo chown jenkins:users ~/iscsi_test' % node
    general.eval_returns(cmd)