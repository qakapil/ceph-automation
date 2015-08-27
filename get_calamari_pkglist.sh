#!/bin/bash
set +ex
iosc='osc -A https://api.suse.de'

if [ ! -d ~/workspace/Devel:Storage:1.0:Staging ] ; then
   $iosc checkout Devel:Storage:1.0:Staging
fi

#pkgs_list=$($iosc ls Devel:Storage:1.0:Staging | grep -v ^_)
pkgs_list="calamari-server diamond salt graphite-web python-carbon python-whisper python-djangorestframework calamari-clients python-Jinja2 python-MarkupSafe python-Twisted python-requests"

pushd ~/workspace/Devel:Storage:1.0:Staging
$iosc up

declare -a pkgs_arr=();
for i in $pkgs_list; do
        pkg_diff=`$iosc rdiff Devel:Storage:1.0:Staging $i Devel:Storage:1.0 $i | cat`
        if [ -n "$pkg_diff" ]; then
                revision=`$iosc info $i | cat | grep Revision | awk '{print $2}'`
                echo package $i:$revision will be copypacd
                pkgs_arr=("${pkgs_arr[@]}" $i:$revision)
        else
            echo package $i is not changed
        fi
done

export pkgs_arr
echo If suite passes, following packages will be copypac\'d:${pkgs_arr[@]}
popd

