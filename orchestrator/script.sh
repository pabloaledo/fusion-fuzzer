mkdir -p test/{local,bin}
( cd test;  python ../../graphcontraints/graph.py > test.pattern )
( cd test/local;  ../../../dtsimulator/dtsimulator ../test.pattern )
( cd test/local; ls -l | grep -v list | awk '{$2=""; $3=""; $4=""; $6=""; $7=""; $8=""; print}' > list )
( cd test/local; md5sum * | grep -v md5 > md5s )
cp ../dtsimulator/dtsimulator test/bin
echo "/test/bin/dtsimulator /test/test.pattern"                                                                >  test/test.sh
echo "ls -l | grep -v list | awk '{\$2=\"\"; \$3=\"\"; \$4=\"\"; \$6=\"\"; \$7=\"\"; \$8=\"\"; print}' > list" >> test/test.sh
rm -fr ~/workspace/fusionfs/tests/random_test
cp -r test ~/workspace/fusionfs/tests/random_test
(cd ~/workspace/fusionfs/tests; ./run_tests.sh --store=s3 --bucket=fusionfs-ci random_test)
(cd ~/workspace/fusionfs/tests/random_test/external_docker_folder; md5sum $(ls * | grep -v fake) > md5s)
