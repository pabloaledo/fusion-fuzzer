rm -fr test
mkdir -p test/{local,bin}
echo "generating"
( cd test; timeout 25s python ../../graphcontraints/graph.py | tee both.pattern )
if [ $(cat test/both.pattern | wc -l) -gt 0 ]
then
    ( cd test;  cat both.pattern | awk '$1 == -1{print}' > init.pattern )
    ( cd test;  cat both.pattern | awk '$1 != -1{print}' > test.pattern)
    echo "run local"
    ( cd test/local;  ../../../dtsimulator/dtsimulator ../init.pattern )
    ( cd test/local;  ../../../dtsimulator/dtsimulator ../test.pattern )
    ( cd test/local; ls -l | grep -v list | grep -v md5s | awk '{$1=""; $2=""; $3=""; $4=""; $6=""; $7=""; $8=""; print}' > list )
    ( cd test/local; echo fake > fake; md5sum * | grep -v md5s > md5s )
    \cp ../dtsimulator/dtsimulator test/bin
    echo "/test/bin/dtsimulator /test/test.pattern"                                                                                         >  test/test.sh
    echo "ls -l | grep -v list | grep -v fake | awk '{\$1=\"\"; \$2=\"\"; \$3=\"\"; \$4=\"\"; \$6=\"\"; \$7=\"\"; \$8=\"\"; print}' > list" >> test/test.sh
    echo "FROM ubuntu:22.04" > test/Dockerfile
    echo "find -not -iname fake -delete" > test/init.sh
    echo "/test/bin/dtsimulator /test/init.pattern" >> test/init.sh
    [ -e $FUSION_S3FS/tests/random_test/ ] && find $FUSION_S3FS/tests/random_test/ -not -iname fake -delete
    rm -fr $FUSION_ROOT/tests/random_test
    cp -r test $FUSION_ROOT/tests/random_test
    export AWS_S3_ENDPOINT=http://172.17.0.2:9000
    export AWS_ACCESS_KEY_ID=minioadmin
    export AWS_SECRET_ACCESS_KEY=minioadmin
    echo "run fusion"
    (cd $FUSION_ROOT/tests; ./run_tests.sh --store=s3 --bucket=fusionfs-ci random_test)
    (cd $FUSION_ROOT/tests/random_test/external_docker_folder; md5sum * > md5s)
    md51=$(md5sum $FUSION_ROOT/tests/random_test/local/md5s | awk '{print $1}')
    md52=$(md5sum $FUSION_ROOT/tests/random_test/external_docker_folder/md5s | awk '{print $1}')

    [ $md51 = $md52 ] && echo '\e[32m SAME RESULTS \e[0m'
    [ $md51 != $md52 ] && echo '\e[31m DIFFERENT RESULTS \e[0m'
    [ $md51 != $md52 ] && tar -cvzf test.backup.`date +%y%m%d-%H%M%S`.tgz test

    ( cat test/both.pattern; echo ) >> all.patterns
fi

[ -e /tmp/pause ] && echo "\e[31m ===== pause =====\e[0m"
while [ -e /tmp/pause ] ; do sleep 10; done
