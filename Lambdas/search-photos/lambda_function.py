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
HOST = 'search-photos-wxge6trfpbu3g36xdqsrgqssxa.us-east-1.es.amazonaws.com'
cred = boto3.Session().get_credentials()
service = 'es'

def lambda_handler(event, context):

    print ('event : ', event)

    q1 = event["queryStringParameters"]['q']
        
    print("q1:", q1 )
    labels = get_labels(q1)
    print("labels", labels)
    if len(labels) != 0:
        img_paths = get_photo_path(labels)

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
            'body': {
                'imagePaths':img_paths,
                'userQuery':q1,
                'labels': labels,
            },
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

    
def get_photo_path(keys):
    
    
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
                    output.append('https://s3.amazonaws.com/photo-storage/'+key)
    print (output)
    return output  