import base64
from errno import ENOANO
from urllib import response
import boto3
import cv2
import io
import os
from imageio import imread
from botocore.exceptions import ClientError
import time
import uuid
import subprocess

AWS_ACCESS_KEY_ID = "AKIA5VS4VY4J64VCYANU"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = 'us-east-1'

def uploadImageToS3(imagePath, imageLabel, imageId):
    bucket = "inputbucketcloud9"

    s3client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
    
    object_name = os.path.basename(imagePath)

    try:
        response =  s3client.upload_file(imagePath, bucket, object_name)
    except ClientError as e:
        return False
    
    try:
        s3client.put_object(Body=imageLabel, Bucket='outputbucketcloud9', Key=imageId)
    except ClientError as e:
        return False
    
    return True

try:
    sqs_client = boto3.client('sqs', aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

    queueURL = "https://sqs.us-east-1.amazonaws.com/939718461203/InputQueue"

    response = sqs_client.receive_message(
        QueueUrl=queueURL,
        MaxNumberOfMessages=1,
        MessageAttributeNames=['All']
    )

    if 'Messages' not in response:
        print("No images. Exiting.")
        exit(0)

    encoded_msg = response['Messages'][0]
    b64_string = str.encode(encoded_msg['Body'])

    img = imread(io.BytesIO(base64.b64decode(b64_string)))

    cv2_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    imageid = ''
    if 'MessageAttributes' in encoded_msg:
        imageid = encoded_msg['MessageAttributes']['ImageId']['StringValue']
    else:
        imageid = str(uuid.uuid4())

    image_name = "image_" + imageid + ".jpg"
    model_dir = '/home/ubuntu/classifier/'

    os.chdir(model_dir)
    cv2.imwrite(image_name, cv2_img)

    print("Saved image with id: ", imageid)

    cmd = "python3 " + model_dir + "image_classification.py " + model_dir + image_name
    classify_result = subprocess.getoutput(cmd)

    print(classify_result)
    #Output SQS
    res_array = classify_result.split(',')
    image_label = res_array[1]

    outputQueueURL = "https://sqs.us-east-1.amazonaws.com/939718461203/OutputQueue"

    response = sqs_client.send_message(
            QueueUrl=outputQueueURL,
            MessageAttributes={
                'ImageId': {
                    'DataType': 'String',
                    'StringValue': imageid
                }
            },
            MessageBody = image_label
        )
    
    uploadImageToS3(model_dir + image_name, classify_result, imageid)

    cmd = "rm -f " + model_dir + image_name
    subprocess.getoutput(cmd)

    receipt_handle = encoded_msg['ReceiptHandle']

    # Delete received message from queue
    sqs_client.delete_message(
        QueueUrl=queueURL,
        ReceiptHandle=receipt_handle
    )
except Exception as e:
    print("Got Exception ", e)
    time.sleep(5)
