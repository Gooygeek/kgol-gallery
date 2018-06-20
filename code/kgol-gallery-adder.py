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
import sys
import boto3
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

BUCKET = os.environ['BUCKET']
WATCH_KEY_PREFIX = os.environ['WATCH_KEY_PREFIX']
PUT_KEY_PREFIX = os.environ['PUT_KEY_PREFIX']
RANDOM_NAME_LENGTH = os.environ['RANDOM_NAME_LENGTH']
AUX_FILES_PREFIX = os.environ['AUX_FILES_PREFIX']
TABLE = os.environ['TABLE']
LIST_OF_TAGS = os.environ['LIST_OF_TAGS']
VERBOSE_LOGGING = os.environ['VERBOSE_LOGGING']
VERBOSE_LOGGING = True if ((VERBOSE_LOGGING == 'True') or (VERBOSE_LOGGING == 'true') or (VERBOSE_LOGGING == 'TRUE')) else False


def generate_random_name(length):
    """
    Generates a random sequence of uppercase letters and numbers of desired length.

    Inputs:
        lenght [Int] - The desired length of the string

    Outputs:
        randomName [String] - A random string of letters and numbers
    """
    # Converts a list of random choices created by list comprehension into a string
    randomName = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(int(length)))
    return randomName


def get_new_images():
    """
    Gets a list of filenames (including the path) from the designated watch folder.

    Outputs:
        newImages['Contents'][1:] [List][String] - A list of filenames (including the path).
    """
    newImages = s3.list_objects_v2(Bucket=BUCKET, EncodingType='url', Prefix=WATCH_KEY_PREFIX)
    return newImages['Contents'][1:]


def parse_name_to_tags(image):
    """
    Gets a list of tags based on the filename of the image being evaulated.
        All tags to be added should be seperated by spaces.
        Assumes that the first word is an identifier and will be ingored.
        Assumes the passed filename contains the path.

    Inputs:
        image [String] - The name of the image being added.

    Outputs:
            tags [List][String] - A list of tags taken from the filename.
            image[dotIndex:] [String] - The images file extention (e.g. '.png').
    """
    # TODO: Handle digits i.e. NO NUMBERS ALLOWED

    # Initiate some variables used in the loop and keeping track of special characters
    curCharIndex, curChar = len(image), ''
    slashIndex, dotIndex, notAllFound = 0, 0, True

    # Unitl the start of the file name is found (end of the path)
    while notAllFound:
        # Go back by one character
        curCharIndex = curCharIndex - 1
        curChar = image[curCharIndex]

        # If the character is a dot, then the start of the file extention must have been found
        if curChar == '.':
            dotIndex = curCharIndex

        # If a forwards slash is found, then the end of the path (start of the filename) must have been found
        if curChar == '/':
            slashIndex, notAllFound = curCharIndex, False

    # Convert the string of tags from the file name is to a list of tags via a splice.
    # Note that the spaces are converted to '+' in theis format so the tags are seperated by '+'s
    #    hence the string needs to be split based on that
    tags = image[slashIndex+1:dotIndex].split('+')[1:]
    return [tags, image[dotIndex:]]


def get_current_tags():
    """
    Opens the list of currently recored dbTags

    Outputs:
        curTags [List][String] - The tags that are currently known
    """
    # Note that we only need the body of the response
    res = s3.get_object(Bucket=BUCKET, Key='/'.join([AUX_FILES_PREFIX, LIST_OF_TAGS]))['Body']

    # Interpret the string representation of a list returned from S3 into a proper list
    #     after first converting from a byte representation of a srting to utf-8
    curTags = ast.literal_eval(str(res.read(), 'utf-8'))
    # The http streaming body should be closed for good practice
    res.close()
    return curTags


def update_tags_list(curTags, newTags):
    """
    Merge the current list of tags with the ones associated with the current image

    Inputs:
        curTags [List][String] - The current list of tags
        newTags [List][String] - The list of tags to be merged into curTags

    Outputs:
        curTags [List] - The merged list of tags
    """
    # Merge the lists by using sets to remove duplicates and then add the new items to the old list.
    curTags = curTags + list(set(newTags)-set(curTags))
    return curTags


def neutralise_tag(tagName):
    """
    Appends '_dbSafe' to the end of the tag so it can be used in DynamoDB and can be searched
        Note that the searched tags must also be neutralisted

    Inputs:
        tagName - [String] - The original tag name that is potentially dangerous to use,
        hence it's getting neutralised

    Outputs:
        neutralisedTagName - [String] - A string that is predicatable and guaranteed to not conflict with DynamoDB Reserved words
    """
    neutralisedTagName = ''.join([tagName, '_dbSafe'])
    return neutralisedTagName


def add_to_db(randomName, tags):
    """
    Add the tags lookup line to the DB for the evaluated image

    Input:
        randomName [String] - The new name of the image to be saved as
        tags [List][String] - A list of the tags associated with this image
    """
    dbTags = {'Id':{'S':str(randomName)}}
    for tag in tags:
        neutralisedTag = neutralise_tag(tag)
        dbTags[neutralisedTag]={'S':'Y'}

    dynamodb.put_item(TableName=TABLE, Item=dbTags)
    if VERBOSE_LOGGING : print("Added: "+randomName+", with tags:"+str(tags)+", to DB.")
    return


def move_to_s3(image, randomName):
    """
    Adds the current image being evaluated to the main gallery folder

    Inputs:
        image [String] - Key prefix of the image being evaluated
        randomName [String] - Name to save the image as
    """
    try:
        oldImageKey = image.replace('+', ' ')
        s3.copy_object(
            Bucket = BUCKET,
            Key = '/'.join([PUT_KEY_PREFIX, randomName]),
            CopySource = {'Bucket':BUCKET,'Key': oldImageKey}
        )
    except:
        if VERBOSE_LOGGING : print("Unable to copy image")
        return
    try:
        s3.delete_object(Bucket = BUCKET, Key=oldImageKey)
        return
    except:
        if VERBOSE_LOGGING : print("Unable to delete image, rolling back...")
        try:
            s3.delete_object(Bucket = BUCKET, Key='/'.join([PUT_KEY_PREFIX, randomName]))
            if VERBOSE_LOGGING : print("Done")
        except:
            if VERBOSE_LOGGING : print("Unable to rollback")
    return


def save_updated_tags_list(curTags):
    """
    Saves the list of tags that have been updated back into s3

    Input:
        curTags [List][String] - The list of tags to save
    """
    # TODO: Sort Alphabetically before saving

    s3.put_object(Bucket=BUCKET, Key='/'.join([AUX_FILES_PREFIX, LIST_OF_TAGS]), Body=str(curTags))
    return


def lambda_handler(event, context):
    """
    Function called when lambda is run, calls main execution flow

    Inputs:
        event [Object] - Lambda call information
        context [Object] - Current execution infomration
    """

    newImages = [image['Key'] for image in get_new_images()]

    curTags = get_current_tags()

    for image in newImages:
        [tags, fileExtention] = parse_name_to_tags(image)
        curTags = update_tags_list(curTags, tags)
        # randomName becomes a combination of a random string and the images filetype extention
        randomName = ''.join([generate_random_name(RANDOM_NAME_LENGTH), fileExtention])
        add_to_db(randomName, tags)
        move_to_s3(image, randomName)

    save_updated_tags_list(curTags)

    return 'Error Free Execution'
