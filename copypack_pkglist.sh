#!/bin/bash
set +ex
copypac="osc  -A https://api.suse.de copypac --expand --keep-link"
echo following packages are getting copypac\'d:${pkgs_arr[@]}
for j in ${pkgs_arr[@]}; do
        var=":"
        pkg=${j%${var}*}
        rev=${j#*${var}}
        $iosc copypac Devel:Storage:1.0:Staging $pkg -r $rev Devel:Storage:1.0
done
