import urllib
import re
import sys
from launch import launch
import general

ceph_deps = (
     'ceph',
     'ceph-deploy', 
     'python-remoto',
     'fio',
     'lrbd',
     'patterns-ses',
     'python-radosgw-agent',
     'ses-manual_en',
     'supportutils-plugin-ses'
)

calamari_deps = (
     'calamari-server',
     'diamond',
     'salt',
     'graphite-web',
     'python-carbon',
     'python-whisper',
     'python-djangorestframework',
     'romana',
     'apache2-mod_wsgi',
     'python-Django',
     'python-Mako',
     'python-Pillow',
     'python-alembic',
     'python-apache-libcloud',
     'python-Twisted',
     'python-django-nose',
     'python-django-tagging',
     'python-gevent',
     'python-greenlet',
     'python-msgpack-python',
     'python-nose',
     'python-psycogreen',
     'python-psycopg2',
     'python-salt-testing',
     'python-whisper',
     'python-zerorpc',
)

url = sys.argv[1]
url_x86_64 = url + '/x86_64/'
url_noarch = url + '/noarch/'

text_x86_64 = urllib.urlopen(url_x86_64).read()
rpms_x86_64 = re.findall(r'href="(.[^"]*x86_64.rpm).mirrorlist"', text_x86_64)

text_noarch = urllib.urlopen(url_noarch).read()
rpms_noarch = re.findall(r'href="(.[^"]*noarch.rpm).mirrorlist"', text_noarch)

if sys.argv[2] == 'ceph':
    input_rpms = ceph_deps
elif sys.argv[2] == 'calamari':
    input_rpms = calamari_deps

output_rpms = []

for rpm in input_rpms:
    op_rpm = [rpms_x86_64[i] for i, item in enumerate(rpms_x86_64) if re.match('^%s-[0-9].*.rpm$'%rpm, item)]
    if len(op_rpm) > 1:
        print 'multiple rpms were found - ' + str(op_rpm)
        sys.exit(1)
    elif len(op_rpm) == 1:
        rpm_url = url_x86_64+op_rpm[0]
        cmd = 'rpm -q -p --qf "%{DISTURL}\n" '+rpm_url
        stdout, stderr = general.eval_returns(cmd)
        if 'Staging' in stdout:
            rev = stdout.split('/')[-1].split('-')[0]
            op = '%s:%s' % (rpm,rev)
            output_rpms.append(op)

for rpm in input_rpms:
    op_rpm = [rpms_noarch[i] for i, item in enumerate(rpms_noarch) if re.match('^%s-[0-9].*.rpm$'%rpm, item)]
    if len(op_rpm) > 1:
        print 'multiple rpms were found - ' + str(op_rpm)
        sys.exit(1)
    elif len(op_rpm) == 1:
        rpm_url = url_noarch+op_rpm[0]
        cmd = 'rpm -q -p --qf "%{DISTURL}\n" ' +rpm_url
        stdout, stderr = general.eval_returns(cmd)
        if 'Staging' in stdout:
            rev = stdout.split('/')[-1].split('-')[0]
            op = '%s:%s' % (rpm,rev)
            output_rpms.append(op)

print ' '.join(output_rpms)
