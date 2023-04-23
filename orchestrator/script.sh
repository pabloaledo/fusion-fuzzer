rm -fr test
mkdir -p test/{local,bin}
( cd test;  python ../../graphcontraints/graph.py > test.pattern )
( cd test/local;  ../../../dtsimulator/dtsimulator ../test.pattern )
( cd test/local; ls -l | grep -v list | awk '{$1=""; $2=""; $3=""; $4=""; $6=""; $7=""; $8=""; print}' > list )
( cd test/local; md5sum * | grep -v md5s > md5s )
cp ../dtsimulator/dtsimulator test/bin
echo "/test/bin/dtsimulator /test/test.pattern"                                                                >  test/test.sh
echo "ls -l | grep -v list | grep -v fake | awk '{\$1=\"\"; \$2=\"\"; \$3=\"\"; \$4=\"\"; \$6=\"\"; \$7=\"\"; \$8=\"\"; print}' > list" >> test/test.sh
echo "FROM ubuntu:22.04" > test/Dockerfile
echo "rm -fr *" > test/init.sh
rm -fr ~/workspace/fusionfs/tests/random_test
cp -r test ~/workspace/fusionfs/tests/random_test
(cd ~/workspace/fusionfs/tests; ./run_tests.sh --store=s3 --bucket=fusionfs-ci random_test)
(cd ~/workspace/fusionfs/tests/random_test/external_docker_folder; md5sum $(ls * | grep -v fake) > md5s)
md51=$(md5sum ~/workspace/fusionfs/tests/random_test/local/md5s | awk '{print $1}')
md52=$(md5sum ~/workspace/fusionfs/tests/random_test/external_docker_folder/md5s | awk '{print $1}')

[ $md51 = $md52 ] && echo '\e[32m SAME RESULTS \e[0m'
[ $md51 != $md52 ] && echo '\e[31m DIFFERENT RESULTS \e[0m'
[ $md51 != $md52 ] && bak test
#md5sum ~/workspace/fusionfs/tests/random_test/{local/md5s,external_docker_folder/md5s}
#meld ~/workspace/fusionfs/tests/random_test/{local/md5s,external_docker_folder/md5s}
#meld ~/workspace/fusionfs/tests/random_test/{local/list,external_docker_folder/list}
