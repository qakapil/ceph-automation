import os
import subprocess
import time
import signal
import logging

log = logging.getLogger(__name__)

def launch(**kwargs):
    origWD = None
    executionString = kwargs.get('cmd', None)
    env = kwargs.get('env', None)
    timeout = kwargs.get('timeout', None)
    workdir = kwargs.get('cwd', None)
    if env == None:
        env = os.environ
    if timeout == None:
        timeout = 60

    if executionString == None:
        return 256,"",""
    # Now handle directory changes
    if workdir != None:
        origWD = os.getcwd()
        os.chdir(workdir)
    log.debug("executing the command "+ executionString)
    process = subprocess.Popen([executionString], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=env)
    
    if origWD != None:
        os.chdir(origWD)
    processRc = None
    handleprocess = True
    counter = 0
    stdout = ''
    stderr = ''
    while handleprocess:
        counter += 1
        cout,cerr = process.communicate()
        stdout += cout
        stderr += cerr
        process.poll()
        processRc = process.returncode
        if processRc != None:
            break
        if counter == timeout:
            os.kill(process.pid, signal.SIGQUIT)
        if counter > timeout:
            os.kill(process.pid, signal.SIGKILL)
            processRc = -9
            break
        time.sleep(1)
    return (processRc,stdout,stderr)
        
        