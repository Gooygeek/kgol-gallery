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


def generate_page(images, allTags):
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

    #
    splitPage = TEMPLATE.split('<+CURTAGS+>')
    CURTAGS_HTML = ''

    for tag in allTags:
        CURTAGS_HTML += '{TAG} '.format(TAG=tag)
    CURTAGS_HTML = CURTAGS_HTML[:-1]

    TEMPLATE = ''.join([splitPage[0], CURTAGS_HTML, splitPage[1]])

    #
    splitPage = TEMPLATE.split('<+ALLTAGS+>')
    ALLTAGS_HTML = ''
    TAG_HTML = """<div class="tag-item">
                    <div class="tag-text">
                        {0}
                    </div>
                    <button class="add-pTag tag-button" onClick="addPTag('{0}')">
                        +
                    </button>
                    <button class="add-nTag tag-button" onClick="addNTagt('{0}')">
                        &minus;
                    </button>
                </div>"""

    encodedTagsList = s3.get_object(
        Bucket=BUCKET, Key='/'.join([AUX_FILES_PREFIX, LIST_OF_TAGS]))['Body']

    tagList = ast.literal_eval(str(encodedTagsList.read(), 'utf-8'))

    for tag in tagList:
        ALLTAGS_HTML += TAG_HTML.format(str(tag))

    TEMPLATE = ''.join([splitPage[0], ALLTAGS_HTML, splitPage[1]])

    #
    splitPage = TEMPLATE.split('<+IMAGES+>')
    IMAGES_HTML = ''

    for image in images:
        IMAGES_HTML += "<div class='image item'><a href='" + '/'.join([
            URL_PREFIX, IMAGE_KEY_PREFIX, image
        ]) + "'data-lightbox='MLP'><img src='" + '/'.join(
            [URL_PREFIX, IMAGE_KEY_PREFIX, image]) + "'></a></div>"

    TEMPLATE = ''.join([splitPage[0], IMAGES_HTML, splitPage[1]])

    #
    page = TEMPLATE

    return page


def lambda_handler(event, context):
    print(json.dumps(event))

    try:
        # get tags from query
        [pTags, nTags] = parse_tags_from_event(event)

        # get image names from dynamodb
        images = get_images_from_tags(pTags, nTags)

        # generate a page
        page = generate_page(images, pTags + nTags)

        # serve the page
        s3.put_object(
            Bucket='kgol-image-gallery', Key='page.html', Body=str(page))

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
        return (errPage)
