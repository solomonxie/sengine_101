#!make
.PHONY: init
include envfile
include envfile-local

#######################################################################
#                     LOCAL DEVELOPMENT UTILITIES                     #
#######################################################################
root:
	# sudo su root
	echo "RUNNING IN root..."

init:
	@bash init.sh

set-env:
	# For manuall debug in shell (not working in makefile, need to copy/paste manually)
	# REF: https://zwbetz.com/set-environment-variables-in-your-bash-shell-from-a-env-file/
	export $(grep -v '^#' ./envfile | xargs) > /dev/null
	export $(grep -v '^#' ./envfile-local | xargs) > /dev/null
	@echo OK


#######################################################################
#                          CELERY TASK QUEUE                          #
#######################################################################
task-worker:
	celery -A scraping.queue.tasks worker -E --loglevel=INFO

dispatch-hello:
	python -m scraping.queue.tasks


dispatch-periodic-hello:
	celery -A scraping.queue.tasks beat



#######################################################################
#                        MINIO SELF HOSTED S3                         #
#######################################################################
minio-build:
	#REF: https://min.io/download#/linux
	#REF: https://min.io/download#/macos
	#Server
	mkdir -p ${MINIO_EXE_DIR} ||true
	[ ! -e ${MINIO_EXE_DIR}/minio ] && wget ${MINIO_DOWNLOAD_URL} -O ${MINIO_EXE_DIR}/minio ||true
	chmod +x ${MINIO_EXE_DIR}/minio ||true
	#Client
	[ ! -e ${MINIO_EXE_DIR}/mc ] && wget ${MC_DOWNLOAD_URL} -O ${MINIO_EXE_DIR}/mc ||true
	chmod +x ${MINIO_EXE_DIR}/mc ||true

minio-server:
	@#PREPARE ENVIRONMENT
	@[ ! -z "${MINIO_ROOT_USER}" ] || exit 128
	@[ ! -z "${MINIO_ROOT_PASSWORD}" ] || exit 128
	@[ ! -z "${MINIO_S3_ACCESS_KEY}" ] || exit 128
	@[ ! -z "${MINIO_S3_SECRET_KEY}" ] || exit 128
	@[ ! -z "${MINIO_MY_STORAGE_DIR}" ] || exit 128
	@mkdir -p ${MINIO_MY_STORAGE_DIR} ||true
	nohup ${MINIO_EXE_DIR}/minio server ${MINIO_MY_STORAGE_DIR} --address "${MINIO_API_ADDR}" --console-address "${MINIO_WEB_CONSOLE_ADDR}" > ${MINIO_LOG_PATH} 2>&1 &
	@echo "START RUNNING MINIO IN THE BACKGROUND..."
	@#[ "`uname -s`" = "Darwin" ] && tail -f ${MINIO_LOG_PATH}  # Mac only
	@echo "OK."

minio-add-cred:
	@#ADD HOST
	# REF: https://docs.min.io/minio/baremetal/reference/minio-cli/minio-mc/mc-alias.html
	@mc alias set ${MINIO_HOST_ALIAS}/ http://${MINIO_API_ADDR} ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}
	@#ADD USER
	# REF: https://docs.min.io/minio/baremetal/reference/minio-cli/minio-mc-admin/mc-admin-user.html
	@mc admin user add ${MINIO_HOST_ALIAS} ${MINIO_S3_ACCESS_KEY} ${MINIO_S3_SECRET_KEY}
	@#TEST
	@mc ls ${MINIO_HOST_ALIAS}
	@echo "OK."

minio-add-bucket:
	#REF: https://docs.min.io/minio/baremetal/reference/minio-cli/minio-mc.html
	mc mb -p ${MINIO_HOST_ALIAS}/${MINIO_BUCKET_NAME} ||true
	mc ls ${MINIO_HOST_ALIAS}/${MINIO_BUCKET_NAME}
	@echo "OK."

minio: minio-build minio-server minio-add-cred minio-add-bucket
	echo "OK."

#######################################################################
#                          EFS CLOUD STORAGE                          #
#######################################################################
#REF: https://docs.aws.amazon.com/efs/latest/ug/efs-mount-helper.html
#REF: https://docs.aws.amazon.com/zh_cn/efs/latest/ug/wt1-test.html
#REF: https://stackoverflow.com/questions/49762840/unable-to-mount-efs-on-ec2-instance-connection-timed-out-error
#REF: https://www.youtube.com/watch?v=I9GO3mYeNAM
#STEPS: CREATE EFS > SELECT SAME REGION & ZONE! > SELECT SAME SEC-GROUP > ADD NFS TO SEC-GROUP > ATTACH THROUGH CLI
efs:
	# PREPARE
	apt install nfs-common -y
	apt install python3-pip
	pip3 install botocore
	#REF: https://docs.aws.amazon.com/efs/latest/ug/installing-amazon-efs-utils.html#installing-other-distro
	apt install binutils -y
	git clone https://github.com/aws/efs-utils
	cd efs-utils
	./build-deb.sh
	yes| apt install ./build/amazon-efs-utils*deb
	# START TO MOUNT
	mkdir ${EFS_MOUNT_DIR} ||true
	echo '${EFS_ID}.efs.${EFS_ZONE}.amazonaws.com:/ ${EFS_MOUNT_DIR} efs defaults,_netdev 0 0' >> /etc/fstab
	mount -a
	# mount -t efs -o tls fs-YOUR_EFS_ID:/ /myefs
	mount |grep ${EFS_MOUNT_DIR}
	df -h |grep ${EFS_MOUNT_DIR}
	chmod go+rw ${EFS_MOUNT_DIR}
	mkdir -p ${EFS_MOUNT_DIR}/log
	mkdir -p ${EFS_MOUNT_DIR}/db
	mkdir -p ${EFS_MOUNT_DIR}/bin
	touch ${EFS_MOUNT_DIR}/README.txt
	wget http://speedtest-nyc1.digitalocean.com/100mb.test -O ${EFS_MOUNT_DIR}/100mb.test


#######################################################################
#                              DATABASE                               #
#######################################################################
#REF: https://hub.docker.com/_/postgres
pg:
	yes| apt install pgcli
	docker run --restart always \
		--name pg \
		-p ${PG_PORT}:5432 \
		-v ${EFS_MOUNT_DIR}/pg:/var/lib/postgresql/data \
		-e PGDATA=/var/lib/postgresql/data/pgdata \
		-e POSTGRES_USER=${PG_USER} \
		-e POSTGRES_PASSWORD=${PG_PASSWORD} \
		-d postgres postgres -c log_statement=all

#REF: https://hub.docker.com/_/redis
redis:
	yes| apt install redis-tools
	docker run --restart always \
		--name rd \
		-p ${REDIS_PORT}:6379 \
		-v ${EFS_MOUNT_DIR}/redis:/data \
		-d redis:alpine \
		redis-server --appendonly yes

#REF: https://hub.docker.com/_/mongo
mongo:
	docker run --restart always \
		--name mongo \
		-p ${MONGO_PORT}:27017 \
		-e MONGO_INITDB_ROOT_USERNAME=${MONGO_USER} \
		-e MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD} \
		-v ${EFS_MOUNT_DIR}/mongo:/data/db \
		-d mongo

#REF: https://hub.docker.com/_/mysql
mysql:
	mkdir /myefs/mysql
	docker run --restart always \
		--name mysql \
		-p ${MYSQL_PORT}:3306 \
		-v ${EFS_MOUNT_DIR}/mysql:/var/lib/mysql \
		-e MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD} \
		-e MYSQL_DATABASE=${MYSQL_DEFAULT_DB} \
		-e MYSQL_USER=${MYSQL_USER} \
		-e MYSQL_PASSWORD=${MYSQL_PASSWORD} \
		mysql -h 0.0.0.0

sqlite:
	yes| apt install sqlite sqlite3
	#REF: https://github.com/coleifer/sqlite-web
	mkdir -p ${EFS_MOUNT_DIR}/sqlite ||true
	sqlite_web --host 0.0.0.0 --port 61591 ${EFS_MOUNT_DIR}/sqlite/mysqlite.db > ${EFS_MOUNT_DIR}/log/sqlite.log 2>&1 &

sqlite-web:
	sqlite_web --host 0.0.0.0 --port 61591 ${EFS_MOUNT_DIR}/sqlite/mysqlite.db
	#sqlite_web --host 0.0.0.0 --port 61591 ~/workspace/db/sqlite/mysqlite.db > /tmp/sqlite.log 2>&1 &



nginx:
	yes| apt install nginx ||true
	mkdir -p ${EFS_MOUNT_DIR}/log/nginx ||true
	mkdir -p ${EFS_MOUNT_DIR}/share ||true
	mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf_bak_`date +%F`
	cp ./deploy/efs_nginx.conf /etc/nginx/nginx.conf
	service nginx restart
	service nginx status
