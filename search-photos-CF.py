import json
import boto3
import uuid
import requests
from requests_aws4auth import AWS4Auth
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

headers = { "Content-Type": "application/json" }
region = 'us-east-1'
cred = boto3.Session().get_credentials()
service = 'es'

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

    print(event)
    query = event["queryStringParameters"]["q"]
    # query = query.encode()
    print("[DEBUG]: ", query)
    client = boto3.client('lexv2-runtime')
    response = client.recognize_text(
        botId='H3ZMPDCIMO',
        botAliasId='YA6N4OXZJT',
        localeId='en_US',
        sessionId='testuser',
        text=query
    )
    print("response", response)

    labels = []
    if 'messages' not in response:
        print("No photo collection for query {}".format(query))
    else:
        print ("messages: ",response['messages'][0]['content'])
        slot_val = response['messages'][0]['content'].split(',')
        for value in slot_val:
            if value!=None:
                labels.append(value)

    photos = es_search_photo_by_label(labels)
    print("photos", photos)
    
    
    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"},
        'body': json.dumps(photos),
        'isBase64Encoded': False
    }
