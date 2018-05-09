import os
import json
import boto3

BUCKET = os.environ["BUCKET"]
TABLE = os.environ["TABLE"]
IMAGE_KEY_PREFIX = os.environ["IMAGE_KEY_PREFIX"]
URL_PREFIX = os.environ["URL_PREFIX"]
VERBOSE_LOGGING = os.environ["VERBOSE_LOGGING"]
VERBOSE_LOGGING = True if ((VERBOSE_LOGGING == 'True') or (VERBOSE_LOGGING == 'true') or (VERBOSE_LOGGING == 'TRUE')) else False

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')


def parse_tags_from_event(event):
    """
    Gets a list of positive and negative tags from the search query

    Inputs:
        event [Object] - Contains details about what called the lambda function including the search string

    Outputs:
        pTags [List] - The tags that an image MUST have
        nTags [List] - The tags that are explicity excluded (an image must NOT have)
    """
    pTags, nTags = [], []
    allTags = event['tags'].split(' ')
    for tag in allTags:
        if tag[0] == "-":
            nTags.append(tag[:])
        else:
            pTags.append(tag[:])
    return [pTags, nTags]


def get_images_from_tags(pTags, nTags):
    """
    Queries the dynamodb table for images based on the passed tags.
        NOTE: An image must have ALL the pTags (but not only the pTags) and NONE of the nTags

    Inputs:
        pTags [List] - The tags that an image MUST have
        nTags [List] - The tags that are explicity excluded (an image must NOT have)
    """

    filterExpressionString = ""
    for pTag in pTags:
        filterExpressionString += "attribute_exists(%s) and " % pTag
    for nTag in nTags:
        filterExpressionString += "attribute_not_exists(%s) and" % nTag[1:]
    filterExpressionString = filterExpressionString[:-4]
    imagesResponse = dynamodb.scan(
        TableName=TABLE,
        FilterExpression = filterExpressionString
    )['Items']

    images = []
    for item in imagesResponse:
        images.append(item['Id']['S'])
    return images


def generate_page(images):
    """
    Generates a page containing the images provided

    Inputs:
        images [List] - The name of the images to be added to the page

    Outputs:
        page [string] - An HTML page
    """
    UPPER_HTML = str(s3.get_object(Bucket=BUCKET, Key='/'.join(['code', 'UPPER_HTML']))['Body'].read(), 'utf-8')

    LOWER_HTML = str(s3.get_object(Bucket=BUCKET, Key='/'.join(['code', 'LOWER_HTML']))['Body'].read(), 'utf-8')

    MID_HTML = ""

    for image in images:
        MID_HTML += "<div class='image'><a href='"+'/'.join([URL_PREFIX, IMAGE_KEY_PREFIX, image])+"'data-lightbox='MLP'><img src='"+'/'.join([URL_PREFIX, IMAGE_KEY_PREFIX, image])+"'></a></div>"

    page = UPPER_HTML + MID_HTML + LOWER_HTML
    return page


def lambda_handler(event, context):
    print(json.dumps(event))

    # get tags from query
    [pTags, nTags] = parse_tags_from_event(event)

    # get image names from dynamodb
    images = get_images_from_tags(pTags, nTags)

    # generate a page
    page = generate_page(images)

    # serve the page
    print(page)

    return 'Error Free Execution'
