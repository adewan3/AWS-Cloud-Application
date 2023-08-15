from urllib import response
import uuid
import boto3
import time

AWS_ACCESS_KEY_ID = "AKIA5VS4VY4J64VCYANU"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = 'us-east-1'

AMI_IMAGE_ID = 'ami-0a156aab071a4bdd7'

inputQueueURL = "https://sqs.us-east-1.amazonaws.com/939718461203/InputQueue"
outputQueueURL = "https://sqs.us-east-1.amazonaws.com/939718461203/OutputQueue"

PRIMARY_VM = 'i-0917198dd0bd5a61d'
active_vms = set()

def numVmsNeeded(msgsCount):
    if msgsCount in range(0, 10):
        return 1
    if msgsCount in range(10, 20):
        return 2
    if msgsCount in range(20, 30):
        return 3
    if msgsCount in range(30, 40):
        return 4
    if msgsCount in range(40, 50):
        return 5
    if msgsCount in range(50, 60):
        return 6
    if msgsCount in range(60, 70):
        return 7
    if msgsCount in range(70, 80):
        return 8
    if msgsCount in range(80, 90):
        return 9
    if msgsCount >= 90:
        return 10

def creteVMs(num):
    ec2 = boto3.resource('ec2', aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
    
    res = ec2.create_instances(
        ImageId=AMI_IMAGE_ID, 
        MaxCount=num, 
        MinCount=1, 
        InstanceType="t2.micro", 
        KeyName="WebTierKey", 
        SecurityGroupIds=['sg-0c10833c7d609c7d2']
    )

    instanceIds = []
    for inst in res:
        instanceIds.append(inst.id)

    return instanceIds

def terminateInstances(instances):
    ec2_client = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

    ec2_client.terminate_instances(InstanceIds=instances)


checkCount = 0
while True:
    try:
        sqs_client = boto3.client('sqs', aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
        response = sqs_client.get_queue_attributes(
            QueueUrl=inputQueueURL, 
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        msgsCount = int(response['Attributes']['ApproximateNumberOfMessages'])
        flightCount = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])

        print("Messages Count ", msgsCount, type(msgsCount))
        print("Flight Count ", flightCount, type(flightCount))

        if msgsCount + flightCount == 0:
            print("Messages is 0")
            checkCount = checkCount + 1
            if checkCount == 3:
                instances = list(active_vms)
                if len(instances) == 0:
                    time.sleep(5)
                    continue
                terminateInstances(instances)
                active_vms = set()
            else:
                time.sleep(5)
            continue
        
        checkCount = 0
        numVms = numVmsNeeded(msgsCount)

        if numVms > len(active_vms):
            required = numVms - len(active_vms)
            print("Creating Vms ", required)
            vmIDs = creteVMs(required)

            for id in vmIDs:
                active_vms.add(id)
        
        time.sleep(5)
        continue
    except Exception as e:
        time.sleep(5)
        continue
