#!/bin/bash
set +ex
iosc='osc -A https://api.suse.de'

if [ ! -d ~/workspace/Devel:Storage:2.0:Staging ] ; then
   $iosc checkout Devel:Storage:2.0:Staging
fi

#pkgs_list=$($iosc ls Devel:Storage:2.0:Staging | grep -v ^_)
pkgs_list="ceph ceph-deploy python-remoto python-execnet python-itsdangerous fio"

pushd ~/workspace/Devel:Storage:2.0:Staging
$iosc up

declare -a pkgs_arr=();
for i in $pkgs_list; do
        pkg_diff=`$iosc rdiff Devel:Storage:2.0:Staging $i Devel:Storage:2.0 $i | cat`
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

