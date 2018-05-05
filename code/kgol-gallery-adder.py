################################################################
#
# Author: Kieran Goldsworthy
# Date: 5/5/2018
#
#
#
################################################################
__author__ = "Kieran Goldsworthy"

import os
import json
import random
import string
import ast
import boto3
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

BUCKET = os.environ['BUCKET']
WATCH_KEY_PREFIX = os.environ['WATCH_KEY_PREFIX']
PUT_KEY_PREFIX = os.environ['PUT_KEY_PREFIX']
RANDOM_NAME_LENGTH = os.environ['RANDOM_NAME_LENGTH']
TABLE = os.environ['TABLE']
LIST_OF_TAGS = os.environ['LIST_OF_TAGS']
VERBOSE_LOGGING = os.environ['VERBOSE_LOGGING']
if ((VERBOSE_LOGGING == 'True') or (VERBOSE_LOGGING == 'true')):
    VERBOSE_LOGGING = True
else:
    VERBOSE_LOGGING = False


def generate_random_name():
    """

    """
    randomName = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(int(RANDOM_NAME_LENGTH)))
    return randomName


def get_new_images():
    """

    """
    newImages = s3.list_objects_v2(Bucket=BUCKET, EncodingType='url', Prefix=WATCH_KEY_PREFIX)
    return newImages['Contents'][1:]


def parse_name_to_tags(image):
    """

    """
    curCharIndex = len(image)
    curChar = ''
    slashIndex = 0
    dotIndex = 0
    notAllFound = True
    while notAllFound:
        curCharIndex = curCharIndex - 1
        curChar = image[curCharIndex]
        if curChar == '.':
            dotIndex = curCharIndex
        if curChar == '/':
            slashIndex = curCharIndex
            notAllFound = False
    tags = image[slashIndex+1:dotIndex].split('+')[1:]
    return [tags, image[dotIndex:]]


def get_current_tags():
    """

    """
    res = s3.get_object(Bucket=BUCKET, Key=LIST_OF_TAGS)['Body']
    curTags = ast.literal_eval(str(res.read(), 'utf-8'))
    res.close()
    return curTags


def update_tags_list(curTags, newTags):
    """

    """
    curTags = curTags + list(set(newTags)-set(curTags))
    return curTags


def add_to_db(randomName, tags):
    """

    """
    dbTags = {'Id':{'S':str(randomName)}}
    for tag in tags:
        dbTags[tag]={'S':'Y'}

    dynamodb.put_item(TableName=TABLE, Item=dbTags)
    print("Added: "+randomName+", with tags:"+str(tags)+", to DB.")
    return


def add_to_s3(image, randomName):
    """

    """

    return


def save_updated_tags_list(curTags):
    """

    """
    s3.put_object(Bucket=BUCKET, Key=LIST_OF_TAGS, Body=str(curTags))
    return


def lambda_handler(event, context):
    """

    """
    newImages = [image['Key'] for image in get_new_images()]
    curTags = get_current_tags()

    for image in newImages:
        [tags, fileExtention] = parse_name_to_tags(image)
        curTags = update_tags_list(curTags, tags)
        randomName = ''.join([generate_random_name(), fileExtention])
        add_to_db(randomName, tags)
        # add_to_s3(image, randomName)
    save_updated_tags_list(curTags)

    return 'Error Free Execution'
