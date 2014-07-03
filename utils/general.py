import os, sys
from launch import launch
import logging

log = logging.getLogger(__name__)

def createDirOLD(dirPath):
    if not os.path.isdir(dirPath):
        try:
            os.mkdir(dirPath)
        except  Exception as e:
            log.error("Error while creating the dir: "+dirPath, sys.exc_info()[0])
            raise Exception, e
    else:
        log.info("the directory '%S' already exists")
        

def createDir(dirPath, machineName=None):
    if machineName == None:
        cmd1 = "ls -l %s" % (dirPath)
        if 'var' in dirPath.split('/'):
            cmd2 = "sudo mkdir -p %s" % (dirPath)
        else:
            cmd2 = "mkdir -p %s" % (dirPath)
    else:
        cmd1 = "ssh %s ls -l %s" % (machineName, dirPath)
        if 'var' in dirPath.split('/'):
            cmd2 = "ssh %s sudo mkdir -p %s" % (machineName, dirPath)
        else:
            cmd2 = "ssh %s mkdir -p %s" % (machineName, dirPath)
        
        
    cmd = cmd1
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0 and stderr.strip() == "":
        log.info("directory %s is already present, not creating " % (dirPath))
        return
    cmd = cmd2
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.error("error while creating the directory %s " % (dirPath))
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)