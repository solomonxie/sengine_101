#! bash
touch envfile-prod
touch envfile-dev
touch envfile-local
touch Makefile-local
touch settings_local.py
touch deploy/redis-local.conf

read -p "Enter environment: 1.Prod 2.Dev ==> [2]: " deploy_env

if [[ "$deploy_env" = "1" ]];then
    echo "Generating [Production] environment..."
    cat envfile-prod > envfile-local ||true
elif [[ "$deploy_env" = "2" ]];then
    echo "Generating [Development] environment..."
    cat envfile-dev > envfile-local ||true
else
    echo "Generating [Development] environment..."
    cat envfile-dev > envfile-local ||true
fi

# GENEATE CONFIG FILES FROM TEMPLATE
# REF: https://skofgar.ch/dev/2020/08/how-to-quickly-replace-environment-variables-in-a-file/
cat ./deploy/redis.conf.template |envsubst > ./deploy/redis-local.conf

echo "DONE."
