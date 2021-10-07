#!make
# .PHONY: prepare
include envfile
-include envfile-local

TARGET: prepare

#######################################################################
#                     LOCAL DEVELOPMENT UTILITIES                     #
#######################################################################
root:
	# sudo su root
	echo "RUNNING IN root..."

prepare:
	@bash prepare.sh
	@echo "OK."

set-env:
	# For manuall debug in shell (not working in makefile, need to copy/paste manually)
	# REF: https://zwbetz.com/set-environment-variables-in-your-bash-shell-from-a-env-file/
	@export $(grep -v '^#' ./envfile | xargs) > /dev/null
	@export $(grep -v '^#' ./envfile-local | xargs) > /dev/null
	@echo "OK."

test-env:
	@[ ! -z "${MINIO_ROOT_USER}" ] || exit 128
	@[ ! -z "${MINIO_ROOT_PASSWORD}" ] || exit 128
	@[ ! -z "${MINIO_S3_ACCESS_KEY}" ] || exit 128
	@[ ! -z "${MINIO_S3_SECRET_KEY}" ] || exit 128
	@[ ! -z "${MINIO_MY_STORAGE_DIR}" ] || exit 128
	@echo "OK, ENV READY."


#######################################################################
#                          CELERY TASK QUEUE                          #
#######################################################################
hi-worker:
	celery -A scraping.queue.hello worker -E --loglevel=INFO

hi-dispatch:
	python -m scraping.queue.hello


hi-dispatch-periodic:
	celery -A scraping.queue.hello beat

do-scrape:
	python -m scraping.general_scraper


do-dispatch:
	python -m scraping.queue.tasks


#######################################################################
#                               DATABASE                              #
#######################################################################
hi-redis:
	python -m scraping.common.redis_utils

hi-db:
	python -m scraping.common.db_utils

hi-bucket:
	python -m scraping.common.bucket_utils


#######################################################################
#                        MINIO SELF HOSTED S3                         #
#######################################################################
minio-build: test-env
	#REF: https://min.io/download#/linux
	#REF: https://min.io/download#/macos
	#Server
	mkdir -p ${MINIO_EXE_DIR} ||true
	[ ! -e ${MINIO_EXE_DIR}/minio ] && wget ${MINIO_DOWNLOAD_URL} -O ${MINIO_EXE_DIR}/minio ||true
	chmod +x ${MINIO_EXE_DIR}/minio ||true
	#Client
	[ ! -e ${MINIO_EXE_DIR}/mc ] && wget ${MC_DOWNLOAD_URL} -O ${MINIO_EXE_DIR}/mc ||true
	chmod +x ${MINIO_EXE_DIR}/mc ||true
	@echo "OK."

minio-server:
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
efs: test-env
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
	@echo "OK."


#######################################################################
#                              DATABASE                               #
#######################################################################
#REF: https://hub.docker.com/_/postgres
pg-server: test-env
	@yes| apt install pgcli
	docker run --restart always \
		--name pg \
		-p ${PG_PORT}:5432 \
		-v ${EFS_MOUNT_DIR}/pg:/var/lib/postgresql/data \
		-e PGDATA=/var/lib/postgresql/data/pgdata \
		-e POSTGRES_USER=${PG_USER} \
		-e POSTGRES_PASSWORD=${PG_PASSWORD} \
		-d postgres postgres -c log_statement=all
	@echo "OK."

pg-deploy: test-env
	# FIXME: NOT WORKING YET...
	cp ./database/pg/deploy/001_create_page_meta.sql ${EFS_MOUNT_DIR}/pg/
	docker exec -u ${PG_USER} pg psql createdb mydb
	docker exec -u ${PG_USER} pg psql mydb ${PG_USER} -f /var/lib/postgresql/data/001_create_page_meta.sql
	@echo "OK."

#REF: https://hub.docker.com/_/redis
redis-server: test-env
	yes| apt install redis-tools
	docker run --restart always \
		--name rd \
		-p ${REDIS_PORT}:6379 \
		-v ${EFS_MOUNT_DIR}/redis:/data \
		-d redis:alpine \
		redis-server --appendonly yes
	@echo "OK."

redis-server-mac:
	@[ ! -x $(command -v redis-server) ] && brew install redis ||true
	@[ -x $(command -v redis-server) ] && brew services stop redis ||true
	redis-server ./deploy/redis-local.conf

#REF: https://hub.docker.com/_/mongo
mongo-server: test-env
	docker run --restart always \
		--name mongo \
		-p ${MONGO_PORT}:27017 \
		-e MONGO_INITDB_ROOT_USERNAME=${MONGO_USER} \
		-e MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD} \
		-v ${EFS_MOUNT_DIR}/mongo:/data/db \
		-d mongo
	@echo "OK."

#REF: https://hub.docker.com/_/mysql
mysql-server: test-env
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
	@echo "OK."

sqlite-server: test-env
	yes| apt install sqlite sqlite3
	#REF: https://github.com/coleifer/sqlite-web
	mkdir -p ${EFS_MOUNT_DIR}/sqlite ||true
	sqlite_web --host 0.0.0.0 --port 61591 ${EFS_MOUNT_DIR}/sqlite/mysqlite.db > ${EFS_MOUNT_DIR}/log/sqlite.log 2>&1 &
	@echo "OK."

sqlite-deploy: test-env
	cat ./database/sqlite/deploy/001_create_link_map.sql |sqlite3 ${SQLITE_DB_PATH}
	@echo "OK."


nginx-server: test-env
	yes| apt install nginx ||true
	mkdir -p ${EFS_MOUNT_DIR}/log/nginx ||true
	mkdir -p ${EFS_MOUNT_DIR}/share ||true
	mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf_bak_`date +%F`
	cp ./deploy/efs_nginx.conf /etc/nginx/nginx.conf
	service nginx restart
	service nginx status
	@echo "OK."
