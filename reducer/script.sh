exec_both(){
    rm -fr ./test/local/*
    ( cd test/local;  ../../../dtsimulator/dtsimulator ../init.pattern )
    ( cd test/local;  ../../../dtsimulator/dtsimulator ../test.pattern )
    ( cd test/local; ls -l | grep -v list | grep -v md5s | awk '{$1=""; $2=""; $3=""; $4=""; $6=""; $7=""; $8=""; print}' > list )
    ( cd test/local; md5sum * | grep -v md5s > md5s )
    \cp ../dtsimulator/dtsimulator test/bin
    echo "/test/bin/dtsimulator /test/test.pattern"                                                                >  test/test.sh
    echo "ls -l | grep -v list | grep -v fake | awk '{\$1=\"\"; \$2=\"\"; \$3=\"\"; \$4=\"\"; \$6=\"\"; \$7=\"\"; \$8=\"\"; print}' > list" >> test/test.sh
    echo "FROM ubuntu:22.04" > test/Dockerfile
    echo "rm -fr *" > test/init.sh
    echo "/test/bin/dtsimulator /test/init.pattern" >> test/init.sh
    rm -fr ~/workspace/fusionfs/tests/random_test
    cp -r test ~/workspace/fusionfs/tests/random_test
    (cd ~/workspace/fusionfs/tests; ./run_tests.sh --store=s3 --bucket=fusionfs-ci random_test)
    (cd ~/workspace/fusionfs/tests/random_test/external_docker_folder; md5sum $(ls * | grep -v fake) > md5s)
    md51=$(md5sum ~/workspace/fusionfs/tests/random_test/local/md5s | awk '{print $1}')
    md52=$(md5sum ~/workspace/fusionfs/tests/random_test/external_docker_folder/md5s | awk '{print $1}')
}

reduce_one(){
lines=()
cat test/test.pattern | while read line
do
    lines+=("$line")
done
line_to_delete=$(( RANDOM % ${#lines[@]} + 1 ))

optype=$( echo $lines[$line_to_delete] | cut -d' ' -f2 )
optran=$( echo $lines[$line_to_delete] | cut -d' ' -f3 )

if [ $optype = 1 ] || [ $optype = 2 ]
then
    for linen in $(seq 1 ${#lines[@]} )
    do
        [ $( echo $lines[$linen] | cut -d' ' -f3 ) = $optran ] && unset 'lines[$linen]'
    done
else
        unset 'lines[$line_to_delete]'
fi

rm -fr test/test.pattern
for line in $lines
do
    echo $line >> test/test.pattern
done
}

reduce(){
\cp test/test.pattern test/last_failing.pattern
for n in $(seq 1 10)
do
    echo '====='
    cat test/test.pattern
    echo '====='
    reduce_one
    exec_both
    if [ $md51 = $md52 ]
    then
        \cp test/last_failing.pattern test/test.pattern
    else
        \cp test/test.pattern test/last_failing.pattern
    fi
done
}
