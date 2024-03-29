import json
import os
import time
import logging
import boto3
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

HOST = 'search-photos-cf-63m3zrp5eownredsgwzd27okza.us-east-1.es.amazonaws.com'

region = 'us-east-1'
service = 'es'
cred = boto3.Session().get_credentials()

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')


client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth= AWS4Auth(cred.access_key,cred.secret_key, region, service, session_token=cred.token),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)
        
                    
def lambda_handler(event, context):
    # extract the bucket name and object key from the S3 PUT event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    # call Rekognition to detect labels in the image
    response = rekognition.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket_name,
                'Name': object_key
            }
        }
    )

    # extract the metadata of the S3 object
    s3_object_metadata = s3.head_object(Bucket=bucket_name, Key=object_key)

    print('s3 data', s3_object_metadata)
    
    # extract the custom labels from the object metadata, if applicable
    custom_labels = []
    if 'x-amz-meta-customlabels' in s3_object_metadata['ResponseMetadata']['HTTPHeaders']:
        custom_labels = s3_object_metadata['ResponseMetadata']['HTTPHeaders']['x-amz-meta-customlabels'].split(',')

    print(custom_labels)
    # create a list of labels detected by Rekognition and append the custom labels
    labels = []
    for label in response['Labels']:
        labels.append(label['Name'])
    labels.extend(custom_labels)

    # create a JSON object with the S3 object information and the labels
    index_data = {
        "objectKey": object_key,
        "bucket": bucket_name,
        "createdTimestamp": str(s3_object_metadata['LastModified']),
        "labels": labels
    }

    # response = client.indices.create('photos')
    # index the JSON object in OpenSearch
    response = client.index(
        index= 'photos',
        body=json.dumps(index_data),
        id = object_key,
        refresh = True
    )

    print('response', response)
    print('hello world!')

    return {
        'statusCode': 200,
        'body': json.dumps('Photo indexed successfully')
    }