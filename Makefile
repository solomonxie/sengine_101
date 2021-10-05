#!make
.PHONY: init
include envfile
include envfile-local

#######################################################################
#                     LOCAL DEVELOPMENT UTILITIES                     #
#######################################################################
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
#                              DATABASE                               #
#######################################################################
sqlite-web:
	sqlite_web --host 0.0.0.0 --port 61591 ~/workspace/db/sqlite/mysqlite.db
	#sqlite_web --host 0.0.0.0 --port 61591 ~/workspace/db/sqlite/mysqlite.db > /tmp/sqlite.log 2>&1 &


#######################################################################
#                        MINIO SELF HOSTED S3                         #
#######################################################################
minio-build:
	#REF: https://min.io/download#/linux
	#REF: https://min.io/download#/macos
	#Server
	mkdir -p ${MINIO_EXE_DIR} ||true
	wget https://dl.min.io/server/minio/release/linux-amd64/minio -O ${MINIO_EXE_DIR}/minio ||true
	chmod +x ${MINIO_EXE_DIR}/minio ||true
	#Client
	wget https://dl.min.io/client/mc/release/linux-amd64/mc -O ${MINIO_EXE_DIR}/mc ||true
	chmod +x ${MINIO_EXE_DIR}/mc ||true

minio-server:
	@#PREPARE ENVIRONMENT
	@[[ ! -z "${MINIO_ROOT_USER}" ]] || exit 128
	@[[ ! -z "${MINIO_ROOT_PASSWORD}" ]] || exit 128
	@[[ ! -z "${MINIO_MY_ACCESS_KEY}" ]] || exit 128
	@[[ ! -z "${MINIO_MY_SECRET_KEY}" ]] || exit 128
	@[[ ! -z "${MINIO_MY_STORAGE_DIR}" ]] || exit 128
	@mkdir -p ${MINIO_MY_STORAGE_DIR} ||true
	nohup ${MINIO_EXE_DIR}/minio server ${MINIO_MY_STORAGE_DIR} --address "${MINIO_API_ADDR}" --console-address "${MINIO_WEB_CONSOLE_ADDR}" > ${MINIO_LOG_PATH} 2>&1 &
	@echo "START RUNNING MINIO IN THE BACKGROUND..."
	@#[[ "`uname -s`" = "Darwin" ]] && tail -f ${MINIO_LOG_PATH}  # Mac only
	@echo "OK."

minio-add-cred:
	@#ADD HOST
	@mc alias set ${MINIO_HOST_ALIAS}/ http://${MINIO_API_ADDR} ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}
	@#ADD USER
	# REF: https://docs.min.io/minio/baremetal/reference/minio-cli/minio-mc-admin/mc-admin-user.html
	@mc admin user add ${MINIO_HOST_ALIAS} ${MINIO_MY_ACCESS_KEY} ${MINIO_MY_SECRET_KEY}
	@#TEST
	@mc ls ${MINIO_HOST_ALIAS}
	@echo "OK."

minio-add-bucket:
	#REF: https://docs.min.io/minio/baremetal/reference/minio-cli/minio-mc.html
	mc mb -p ${MINIO_HOST_ALIAS}/${MINIO_BUCKET_NAME} ||true
	mc ls ${MINIO_HOST_ALIAS}/${MINIO_BUCKET_NAME}
	@echo "OK."

include Makefile-local
