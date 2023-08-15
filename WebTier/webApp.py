from asyncore import file_dispatcher
from email.mime import base
from flask import Flask, request, jsonify
from PIL import Image
import base64
import os
from io import BytesIO
from email.message import Message
from urllib import response
import boto3
import uuid
import time

app = Flask(__name__)

classification_results = {}

@app.route("/queueImage", methods=["POST"])
def process_image():
    try:
        fid = request.files['myfile']

        data = fid.read()

        b64_bytes = base64.b64encode(data)
        b64_string = b64_bytes.decode()

        imagepath = fid.name
        ImageId = os.path.basename(imagepath)

        print("ImageId is : ", ImageId)

        sqs_client = boto3.client('sqs', aws_access_key_id='AKIA5VS4VY4J64VCYANU',
        aws_secret_access_key='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', region_name='us-east-1')

        queueURL = "https://sqs.us-east-1.amazonaws.com/939718461203/InputQueue"

        response = sqs_client.send_message(
            QueueUrl=queueURL,
            MessageAttributes={
                'ImageId': {
                    'DataType': 'String',
                    'StringValue': ImageId
                }
            },
            MessageBody = b64_string
        )

        outputQueueURL = "https://sqs.us-east-1.amazonaws.com/939718461203/OutputQueue"

        while True:
            if ImageId in classification_results:
                label = classification_results[ImageId]
                del(classification_results[ImageId])
                return jsonify({'result': label})

            response = sqs_client.receive_message(
                QueueUrl=outputQueueURL,
                MaxNumberOfMessages=1,
                MessageAttributeNames=['All']
            )

            if 'Messages' not in response:
                time.sleep(5)
                continue

            message = response['Messages'][0]
            result_label = message['Body']
            id = message['MessageAttributes']['ImageId']['StringValue']

            classification_results[id] = result_label

            handle = message['ReceiptHandle']
            sqs_client.delete_message(
                QueueUrl=outputQueueURL,
                ReceiptHandle=handle
            )
    except Exception as e:
        print("Got Exception ", e)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')


'''
python3 multithread_workload_generator.py --num_request 10 --url 'http://127.0.0.1:5000/sendImage' --image_folder '/Users/umamaheshwarreddymalay/Desktop/CloudComputing/images/'

'''