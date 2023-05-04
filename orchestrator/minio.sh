docker run -it --rm -p 9000:9000 -p 9001:9001 quay.io/minio/minio server /data --console-address ":9001"
docker run --entrypoint=/bin/sh minio/mc -c 'mc config host add minio http://172.17.0.2:9000 minioadmin minioadmin && mc mb minio/fusionfs-ci'
