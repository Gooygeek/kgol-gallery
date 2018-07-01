import os
import json
import ast
from random import shuffle
import boto3  #pylint: disable=F0401

s3 = boto3.client('s3')

def lambda_handler(event, context):
    print("request:\n"+str(json.dumps(event)))

    if ('queryStringParameters' in event) and (event['queryStringParameters'] != None) and ('username' in event['queryStringParameters']) and ('password' in event['queryStringParameters']) and (event['queryStringParameters']['username'] == 'Kieran') and (event['queryStringParameters']['password'] == '123456'):
        setAuth = 'yes'
        page = """<!DocType html>
        <body>
            <script>
                window.location = 'https://gallery.kgol.xyz/search';
            </script>
        </body>
        """
    else:
        setAuth = 'no'
        page = str(s3.get_object(Bucket='kgol-image-gallery', Key='aux-files/LOGIN_PAGE.html')['Body'].read(), 'utf8')

    response = {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html; charset=utf-8',
            'Set-Cookie': 'authorisation={AUTH}'.format(AUTH=setAuth)
        },
        'body': str(page)
    }
    return response
