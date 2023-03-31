import json
import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import requests
import urllib.parse
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
    
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

headers = { "Content-Type": "application/json" }
region = 'us-east-1'
lex = boto3.client('lexv2-runtime')
HOST = 'search-photo-qgodteylft6yxnrtionvrcm4c4.us-east-1.es.amazonaws.com'
cred = boto3.Session().get_credentials()
service = 'es'
s3 = boto3.client('s3')

GLOBAL_INDEX = 0
URL = 'https://search-photo-qgodteylft6yxnrtionvrcm4c4.us-east-1.es.amazonaws.com/photos/{}'

def send_signed(method, url, service='es', region='us-east-1', body=None):
    credentials = boto3.Session().get_credentials()
    auth = AWS4Auth(credentials.access_key, credentials.secret_key, 
                  region, service, session_token=credentials.token)

    fn = getattr(requests, method)
    if body and not body.endswith("\n"):
        body += "\n"
    try:
        response = fn(url, auth=auth, data=body, 
                        headers={"Content-Type":"application/json"})
        print(response)
        if response.status_code >= 300:
            raise Exception("{} failed with status code {}".format(method.upper(), response.status_code))
        return response.content
    except Exception:
        raise

def es_search(criteria):
    url = URL.format('_search')
    return send_signed('get', url, body=json.dumps(criteria))

def es_search_photo_by_label(labels):

    photos = list()
    for label in labels:
        res = es_search({"query": {"match": {"labels": label}}})
        photos.extend([h["_source"] for h in json.loads(res)["hits"]["hits"]])
    return photos

def lambda_handler(event, context):

    print ('event : ', event)

    q1 = event["queryStringParameters"]['q']

    print("q1:", q1 )
    labels = get_labels(q1)
    print("labels", labels)
    photos = es_search_photo_by_label(labels)
    
    bucket_name = photos[0]['bucket']
    if len(labels) != 0:
        img_paths = get_photo_path(labels, bucket_name)

    print("img_paths", img_paths)
    if not img_paths:
        return{
            'statusCode':200,
            "headers": {"Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"},
            'body': json.dumps('No Results found')
        }
    else:    
        return{
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"},
            'body': json.dumps({
                'imagePaths':img_paths,
                'userQuery':q1,
                'labels': labels,
            }),
            'isBase64Encoded': False
        }
    
def get_labels(query):
    response = lex.recognize_text(
        botId='H3ZMPDCIMO',
        botAliasId='YA6N4OXZJT',
        localeId='en_US',
        sessionId='testuser',
        text=query
    )
    print("lex-response", response)
    print("lex-response-slots", response['messages'])
    
    labels = []
    if 'messages' not in response:
        print("No photo collection for query {}".format(query))
    else:
        print ("messages: ",response['messages'][0]['content'])
        slot_val = response['messages'][0]['content'].split(',')
        for value in slot_val:
            if value!=None:
                labels.append(value)
    return labels

    
def get_photo_path(keys, bucket_name):
    
    
    es = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth= AWS4Auth(cred.access_key,cred.secret_key, region, service, session_token=cred.token),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)
    
    resp = []
    for key in keys:
        if (key is not None) and key != '':
            searchData = es.search({"query": {"match": {"labels": key}}})
            resp.append(searchData)
    print(resp)
    output = []
    for r in resp:
        if 'hits' in r:
             for val in r['hits']['hits']:
                key = val['_source']['objectKey']
                if key not in output:
                    image_url = s3.generate_presigned_url('get_object', Params={'Bucket':bucket_name, 'Key':key})
                    output.append(image_url)
    print ('output', output)
    return output  