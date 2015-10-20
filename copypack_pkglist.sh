#!/bin/bash
set +ex
iosc='osc -A https://api.suse.de'
#copypac="osc  -A https://api.suse.de copypac --expand --keep-link"
echo following packages are getting copypac\'d:${pkgs_arr[@]}
for j in ${pkgs_arr[@]}; do
        var=":"
        pkg=${j%${var}*}
        rev=${j#*${var}}
        $iosc copypac Devel:Storage:2.0:Staging $pkg -r $rev Devel:Storage:2.0
done
