import boto3
from logging import getLogger

import settings

logger = getLogger(__name__)


class S3Exception(Exception):
    pass


def get_s3_client():
    client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_S3_ACCESS_ID,
        aws_secret_access_key=settings.AWS_S3_ACCESS_SECRET,
        endpoint_url=settings.AWS_S3_ENDPOINT,
        region_name=settings.AWS_S3_REGION,
    )
    return client


def get_s3_resource():
    resource = boto3.resource(
        's3',
        aws_access_key_id=settings.AWS_S3_ACCESS_ID,
        aws_secret_access_key=settings.AWS_S3_ACCESS_SECRET,
        endpoint_url=settings.AWS_S3_ENDPOINT,
        region_name=settings.AWS_S3_REGION,
    )
    return resource


class S3Bucket:
    def __init__(self, bucket=''):
        self.resource = get_s3_resource()
        self.client = get_s3_client()
        self.bucket = bucket or settings.AWS_S3_BUCKET_NAME

    def upload_blob(self, s3_path: str, blob: str):
        try:
            obj = self.resource.Object(self.bucket, s3_path)
            obj.put(Body=blob)
        except Exception as e:
            logger.error('[ S3 DOWNLOAD ] FAILED TO UPLOAD DATA TO: {}, {}'.format(s3_path, e))
            raise S3Exception(e)
        return True

    def download_blob(self, s3_path: str):
        blob = ''
        try:
            obj = self.resource.Object(self.bucket, s3_path)
            body = obj.get()
            blob = body['Body'].read()
        except Exception as e:
            logger.error('[ S3 DOWNLOAD ] FAILED TO GET DATA FROM: {}, {}'.format(s3_path, e))
            raise S3Exception(e)
        return blob

    def create_bucket(self):
        existing = [b['Name'] for b in self.client.list_buckets()['Buckets']]
        if self.bucket not in existing:
            self.resource.create_bucket(Bucket=self.bucket)
            print('Created bucket:', str(self.bucket))
        return self.resource.Bucket(self.bucket).creation_date

    def delete_bucket(self):
        """
        Only used in testing environment
        """
        existing = [b['Name'] for b in self.client.list_buckets()['Buckets']]
        if self.bucket in existing:
            bucket = self.resource.Bucket(self.bucket)
            _ = [key.delete() for key in bucket.objects.all()]
            bucket.delete()

    def list_files(self, path_prefix=None):
        if path_prefix:
            keys = [obj.key for obj in self.resource.Bucket(self.bucket).objects.filter(Prefix=path_prefix)]
        else:
            keys = [obj.key for obj in self.resource.Bucket(self.bucket).objects.all()]
        return keys


def main():
    __import__('pudb').set_trace()
    s3 = S3Bucket()
    result = s3.list_files()
    print(result)


if __name__ == '__main__':
    main()
