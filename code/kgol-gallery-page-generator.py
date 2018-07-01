import os
import json
import ast
from random import shuffle
import boto3  #pylint: disable=F0401

BUCKET = os.environ["BUCKET"]
TABLE = os.environ["TABLE"]
IMAGE_KEY_PREFIX = os.environ["IMAGE_KEY_PREFIX"]
AUX_FILES_PREFIX = os.environ['AUX_FILES_PREFIX']
URL_PREFIX = os.environ["URL_PREFIX"]
LIST_OF_TAGS = os.environ['LIST_OF_TAGS']
VERBOSE_LOGGING = os.environ["VERBOSE_LOGGING"]
VERBOSE_LOGGING = True if ((VERBOSE_LOGGING == 'True')
                           or (VERBOSE_LOGGING == 'true')
                           or (VERBOSE_LOGGING == 'TRUE')) else False

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')


def lambda_handler(event, context):
    print(json.dumps(event))

    try:
        # Gets the cookie from the headers hence getting various information
        Cookies = get_cookies(event)

        # Determine authorisation
        if Cookies['authorisation'] == 'no':
            return (generate_unauthorised_response())

        # get tags from query
        if ('queryStringParameters' in event) and (event['queryStringParameters'] != None) and ('tags' in event['queryStringParameters']):
            [pTags, nTags] = parse_tags(event['queryStringParameters']['tags'])
        else:
            pTags, nTags = [], []

        # get image names from dynamodb
        images = get_images_from_tags(pTags, nTags)

        # Randomise the image order
        isRandom = False
        if (('queryStringParameters' in event) and (event['queryStringParameters'] != None) and ('random' in event['queryStringParameters']) and (event['queryStringParameters']['random'] == 'on')):
            isRandom = True
            shuffle(images)

        # generate a page
        page = generate_page(images, pTags + nTags, isRandom)

        # serve the page
        s3.put_object(
            Bucket='kgol-image-gallery', Key='page.html', Body=str(page))

        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html; charset=utf-8',
                'Set-Cookie': 'JWT=PLACE.HOLDER'
            },
            'body': str(page)
        }
        return (response)

    except Exception as e:
        print('ERROR OCCURED')
        print(e)
        return (generate_error_page())


def get_cookies(event):
    """
    gets the cookies

    Inputs:
        event - [Dict.] - The HTTP request data

    Output:
        Cookies - [Dict.] - The parsed data from the request
    """
    # TODO: USE JWT
    Cookies = {}

    if ('headers' in event) and ('Cookie' in event['headers']):
        rawCookie = event['headers']['Cookie']
        listOfCookies = rawCookie.split(';')
        for cookie in listOfCookies:
            parts = cookie.strip().split('=')
            Cookies[parts[0]] = parts[1]

    return Cookies


def generate_unauthorised_response():
    """
    Used to generate a page when the Authorisation fails

    Output:
        response - [Dict.] - The HTTP response (includes the page and headers)
    """

    unAuthPage = """<!DocType html>
    <body>
        NOT AUTHORISED
    </body>
    """
    response = {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'text/html; charset=utf-8'
        },
        'body': str(unAuthPage)
    }
    return (response)


def parse_tags(tagString):
    """
    Gets a list of positive and negative tags from the search query

    Inputs:
        event [Object] - Contains details about what called the lambda function including the search string

    Outputs:
        pTags [List] - The tags that an image MUST have
        nTags [List] - The tags that are explicity excluded (an image must NOT have)
    """
    pTags, nTags = [], []
    # Removes surrounding whitespace, then splits based on spaces and returns a list
    allTags = tagString.strip().split(' ')
    for tag in allTags:
        if tag != '':
            if tag[0] == '-':
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
        neutralisedTag = neutralise_tag(pTag)
        filterExpressionString += "attribute_exists({TAG}) and ".format(
            TAG=neutralisedTag)
    for nTag in nTags:
        neutralisedTag = neutralise_tag(nTag)
        filterExpressionString += "attribute_not_exists({TAG}) and ".format(
            TAG=neutralisedTag[1:])
    filterExpressionString = filterExpressionString[:-5]
    if filterExpressionString != '':
        imagesResponse = dynamodb.scan(
            TableName=TABLE, FilterExpression=filterExpressionString)['Items']
    else:
        imagesResponse = dynamodb.scan(TableName=TABLE)['Items']

    images = []
    for item in imagesResponse:
        images.append(item['Id']['S'])
    return images


def neutralise_tag(tagName):
    """
    Appends '_dbSafe' to the end of the tag so it can be used in DynamoDB and can be searched
        Note that the searched tags must also be neutralisted

        SUPER IMPORTANT: THIS WILL NOT WORK FOR NUMBERS

    Inputs:
        tagName - [String] - The original tag name that is potentially dangerous to use,
        hence it's getting neutralised

    Outputs:
        neutralisedTagName - [String] - A string that is predicatable and guaranteed to not conflict with DynamoDB Reserved words
    """
    neutralisedTagName = ''.join([str(tagName), '_dbSafe'])
    return neutralisedTagName


def generate_page(images, allTags, isRandom):
    """
    Generates a page containing the images provided

    Inputs:
        images [List] - The name of the images to be added to the page

    Outputs:
        page [string] - An HTML page
    """

    TEMPLATE = str(
        s3.get_object(
            Bucket=BUCKET, Key='/'.join(
                [AUX_FILES_PREFIX, 'TEMPLATE.html']))['Body'].read(), 'utf-8')

    # Add the tags being searched for into the search field.
    CURTAGS_HTML = ''
    for tag in allTags:
        CURTAGS_HTML += '{TAG} '.format(TAG=tag)
    CURTAGS_HTML = CURTAGS_HTML[:-1]

    # Persist randomise checkbox value
    RANDOM_HTML = 'checked' if isRandom else ''

    # Generate the List of Tags as HTML
    ALLTAGS_HTML = ''
    TAG_HTML = """<div class="tag-item">
                    <div class="tag-text">
                        {0}
                    </div>
                    <button class="add-pTag tag-button" onClick="addPTag('{0}')">
                        +
                    </button>
                    <button class="add-nTag tag-button" onClick="addNTag('{0}')">
                        &minus;
                    </button>
                </div>"""

    encodedTagsList = s3.get_object(
        Bucket=BUCKET, Key='/'.join([AUX_FILES_PREFIX, LIST_OF_TAGS]))['Body']

    tagList = ast.literal_eval(str(encodedTagsList.read(), 'utf-8'))

    for tag in tagList:
        ALLTAGS_HTML += TAG_HTML.format(str(tag))

    # Generate the List of Images as HTML
    IMAGES_HTML = ''
    for image in images:
        IMAGES_HTML += "<div class='image item'><a href='" + '/'.join([
            URL_PREFIX, IMAGE_KEY_PREFIX, image
        ]) + "'data-lightbox='MLP'><img src='" + '/'.join(
            [URL_PREFIX, IMAGE_KEY_PREFIX, image]) + "'></a></div>"

    # Add the elements into the template file
    page = TEMPLATE.format(CURTAGS=CURTAGS_HTML, RANDOMCHECKED=RANDOM_HTML, ALLTAGS=ALLTAGS_HTML, IMAGES=IMAGES_HTML)

    return page


def generate_error_page():
    errPage = """<!DocType html>
        <body>
            INTERNAL SERVER ERROR
        </body>
        """
    response = {
        'statusCode': 502,
        'headers': {
            'Content-Type': 'text/html; charset=utf-8'
        },
        'body': str(errPage)
    }
    return response
