import os
import json
import ast
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
        filterExpressionString += "attribute_exists(%s) and " % pTag
    for nTag in nTags:
        filterExpressionString += "attribute_not_exists(%s) and" % nTag[1:]
    filterExpressionString = filterExpressionString[:-4]
    if filterExpressionString != '':
        imagesResponse = dynamodb.scan(
            TableName=TABLE, FilterExpression=filterExpressionString)['Items']
    else:
        imagesResponse = dynamodb.scan(TableName=TABLE)['Items']

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
    START_TO_TAGS = str(
        s3.get_object(
            Bucket=BUCKET, Key='/'.join(
                [AUX_FILES_PREFIX, 'START_TO_TAGS']))['Body'].read(), 'utf-8')

    TAGS_HTML = ""

    encodedTagsList = s3.get_object(Bucket=BUCKET, Key='/'.join([AUX_FILES_PREFIX, LIST_OF_TAGS]))['Body']

    tagList = ast.literal_eval(str(encodedTagsList.read(), 'utf-8'))

    for tag in tagList:
        TAGS_HTML += "<div class='tag-item'>" + str(tag) + "</div>"

    TAGS_TO_IMAGES = str(
        s3.get_object(
            Bucket=BUCKET, Key='/'.join(
                [AUX_FILES_PREFIX, 'TAGS_TO_IMAGES']))['Body'].read(), 'utf-8')

    IMAGES_HTML = ""

    for image in images:
        IMAGES_HTML += "<div class='image item'><a href='" + '/'.join([
            URL_PREFIX, IMAGE_KEY_PREFIX, image
        ]) + "'data-lightbox='MLP'><img src='" + '/'.join(
            [URL_PREFIX, IMAGE_KEY_PREFIX, image]) + "'></a></div>"

    IMAGES_TO_END = str(
        s3.get_object(
            Bucket=BUCKET, Key='/'.join(
                [AUX_FILES_PREFIX, 'IMAGES_TO_END']))['Body'].read(), 'utf-8')

    page = START_TO_TAGS + TAGS_HTML + TAGS_TO_IMAGES + IMAGES_HTML + IMAGES_TO_END

    return page


def lambda_handler(event, context):
    print(json.dumps(event))

    try:
        # get tags from query
        [pTags, nTags] = parse_tags_from_event(event)

        # get image names from dynamodb
        images = get_images_from_tags(pTags, nTags)

        # generate a page
        page = generate_page(images)

        # serve the page
        s3.put_object(Bucket = 'kgol-image-gallery',
            Key = 'page.html',
            Body = str(page)
        )

        return str(page)

    except Exception as e:
        errPage = """<!DocType html>
            <body>
                <script>
                    window.location = 'https://gallery.kgol.xyz/search';
                </script>
            </body>
            """
        print('ERROR OCCURED')
        print(e)
        return(errPage)
