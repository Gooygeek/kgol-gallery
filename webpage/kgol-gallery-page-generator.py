import os
import json
import boto3

BUCKET = os.environ["BUCKET"]
GET_KEY_PREFIX = os.environ["GET_KEY_PREFIX"]
VERBOSE_LOGGING = os.environ["VERBOSE_LOGGING"]
if ((VERBOSE_LOGGING == 'True') or (VERBOSE_LOGGING == 'true') or (VERBOSE_LOGGING == 'TRUE')):
    VERBOSE_LOGGING = True
else:
    VERBOSE_LOGGING = False


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
    return


def get_images_from_tags(pTags, nTags):
    """
    Queries the dynamodb table for images based on the passed tags.
        NOTE: An image must have ALL the pTags (but not only the pTags) and NONE of the nTags

    Inputs:
        pTags [List] - The tags that an image MUST have
        nTags [List] - The tags that are explicity excluded (an image must NOT have)
    """
    return


def generate_page(images):
    """
    Generates a page containing the images provided

    Inputs:
        images [List] - The name of the images to be added to the page

    Outputs:
        page [string] - An HTML page
    """
    # UPPER_HTML =

    # LOWER_HTML =

    MID_HTML = ""

    for image in images:
        MID_HTML =+ "<div class='image'><a href=''"+BUCKET+"/"+image+"'data-lightbox='MLP'><img src='"+BUCKET+"/"+image+"'></a></div>"

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


    return 'Hello from Lambda'
