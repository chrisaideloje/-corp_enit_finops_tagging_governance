import os
import csv
import boto3
import json
import datetime
import os
import smtplib
from email.message import EmailMessage
#from azure.identity import ClientSecretCredential
#from azure.storage.blob import BlobServiceClient
from os import environ
from boto3 import Session as b3session
import botocore
from botocore.config import Config
import sys
import credentials
import logging
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()




# Load AWS credentials
# id = credentials.AWS_ACCESS_KEY_ID
# key = credentials.AWS_SECRET_ACCESS_KEY
# region = credentials.AWS_DEFAULT_REGION


# os.environ['AWS_ACCESS_KEY_ID'] = credentials.AWS_ACCESS_KEY_ID  # Ensure to replace with actual values
# os.environ['AWS_SECRET_ACCESS_KEY'] = credentials.AWS_SECRET_ACCESS_KEY
# os.environ['AWS_DEFAULT_REGION'] = credentials.AWS_DEFAULT_REGION
#id = credentials.AWS_ACCESS_KEY_ID
id = os.getenv("AWS_ACCESS_KEY_ID")
key = os.getenv("AWS_SECRET_ACCESS_KEY")
region = os.getenv("AWS_DEFAULT_REGION")


print(f"Using AWS_ACCESS_KEY_ID: {id}")
print(f"Using AWS_SECRET_ACCESS_KEY: {key}")
print(f"Using AWS_DEFAULT_REGION: {region}")
def create_aws_session():
    """
    Create an AWS session using credentials loaded from the credentials module.
    """
# Create an STS client using permanent credentials
    sts_client = boto3.client(
        'sts',
        aws_access_key_id=id,  # Replace with your IAM access key
        aws_secret_access_key=key,  # Replace with your IAM secret key
        region_name=region  # Replace with your desired region
    )
    print("STS client created using permanent credentials.")
    print(f"Using AWS_ACCESS_KEY_ID: {id}")
    print(f"Using AWS_SECRET_ACCESS_KEY: {key}")
    print(f"Using AWS_DEFAULT_REGION: {region}")
    try:
        
        sts_client.get_caller_identity()
        print("Successfully called get_caller_identity on STS client.") 
    except botocore.exceptions.ClientError as e:
        
        print("Error calling get_caller_identity on STS client:", e)
        sys.exit(1) 
    # Get temporary security credentials
    response = sts_client.get_session_token(DurationSeconds=3600)
    print("Temporary credentials obtained from STS get_session_token call.")
    
    print("Temporary credentials response:", json.dumps(response, indent=4, default=str))
    # Access temporary credentials from the response
    temp_credentials = response['Credentials']

    # Print the temporary credentials
    print("Access Key ID:", temp_credentials['AccessKeyId'])
    print("Secret Access Key:", temp_credentials['SecretAccessKey'])
    print("Session Token:", temp_credentials['SessionToken'])
    print("Expiration:", temp_credentials['Expiration'])

    return boto3.Session(
        aws_access_key_id=temp_credentials['AccessKeyId'],
        aws_secret_access_key=temp_credentials['SecretAccessKey'],
        aws_session_token=temp_credentials['SessionToken'],
        region_name=region
    )

# AWS Organizations client
session = create_aws_session()
org_client = session.client('organizations')


print("Starting")
print(datetime.datetime.now())
# exportDate = datetime.datetime.now().strftime('%Y/%-m/%-d %H:%M')
# exportDateFile = datetime.datetime.now().strftime('%Y%m%d_%H%M')

exportDate = "11Feb2025"
exportDateFile = "11-02-2025"

# Changing OUTPUT_FILENAME env variable
new_output_filename = f"aws/defaultASNTags_{exportDateFile}.csv"
os.environ["OUTPUT_FILENAME"] = new_output_filename
filename = environ.get('OUTPUT_FILENAME')
print(f"filename: {filename}")

# Creating file that contains the name of the file in order to make a github artifact
with open('output_filename.txt', 'w') as file:
    file.write(filename)

# Create the directory if it doesn't exist
os.makedirs(os.path.dirname(filename), exist_ok=True)

# Rebuild the string without the file path
file_name_for_attachment = os.path.basename(filename)
#print(file_name_for_attachment)

# Write header for csv file
with open(filename, 'w', newline='') as file:
    # Create a writer object
    fieldnames = ['source', 'exportDate', 'subscriptionId', 'subscriptionName', 'subscriptionStatus', 'supportgroup',  'resourcecontact', 'environment', 'applicationservicenumber', 'bac', 'sbg', 'sbu', 'sbe']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    # Write the headers to the CSV file
    writer.writeheader()

# Set up the IAM client
iam = boto3.client('iam')

# Get a list of all AWS accounts in the organization

#Get ref of all AWS Accounts and link AccountNumber to AccountName and SBG
# create an Organizations client
#org_client = boto3.client('organizations')

# set the initial value of NextToken to None
accounts = []
next_token = None
accountSBGMappingList = []
# keep making calls to list_accounts until all the accounts have been retrieved
response = org_client.list_accounts()
accounts = response["Accounts"]
while "NextToken" in response:
    response = org_client.list_accounts(NextToken=response["NextToken"])
    accounts.extend(response["Accounts"])
print("Debug after all the all accounts looping")
print(accounts)
#while True:
# call the list_accounts method and pass the NextToken parameter if it has a value
#    if next_token:
#        response = org_client.list_accounts(NextToken=next_token)
#    else:
#        response = org_client.list_accounts()
    #print(response)
#    accounts.extend(response['Accounts'])
#    next_token = response.get('NextToken')
#    if not next_token:
#            break
    # extract the account names and account IDs
    #print(accounts)
for account in accounts:
    #print(account)
    accountID=account["Id"]
    print(accountID)
    accountName=account["Name"]
    accountStatus=account["Status"]
    #If status is not active, then skip
    # if accountStatus != "ACTIVE":
    #     print("Account is not ACTIVE, skipping")
    #     continue
    if accountID == "980840311420":
      accountSBGMappingList.append({'accountID': accountID,'accountName': accountName, 'sbgName': 'CORP', 'accountStatus': "ACTIVE"})
      continue
    ou_response = org_client.list_parents(ChildId=account['Id'])
    ou_responselist = ou_response['Parents']
    for ou in ou_responselist:
        ouinfo = org_client.describe_organizational_unit(OrganizationalUnitId=ou['Id'])
        #print(ouinfo)
        ouNameWithHyphen = ouinfo['OrganizationalUnit']['Name']
        ouName = ouNameWithHyphen.split(' ')[0]
        if ouName == "AmazonManagedServices":
          ouName = "CORP"
        if ouName == "ControlTowerFoundation":
          ouName = "CORP"
        if accountID == "009156179956":
          ouName = "BA"
        if ouName == "DecomissionedAccts":
          ouName = "CORP"
        if ouName == "LZ_Core_Suspended":
          ouName = "CORP"
        if ouName == "EIT":
          ouName = "CORP"
        #print(ouName)
        accountSBGMappingList.append({'accountID': accountID,'accountName': accountName, 'sbgName': ouName, 'accountStatus': accountStatus})
        #print(accountSBGMappingList)

accountCounter=0
# Loop through each account and assume the hon_master_viewer role to query the effective tags
for account in accountSBGMappingList:
    account_id = account['accountID']
    accountName = account['accountName']
    accountStatus = account['accountStatus']
    if accountStatus != "ACTIVE":
        accountCounter += 1
        print("Account Counter "+str(accountCounter))
        print("Account Name"+accountName)
        print("Account is not ACTIVE, Marking fields as NONE and using next account")
        with open(filename, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow({'source': "AWS", 'exportDate': exportDate, 'subscriptionId': account_id, 'subscriptionName': accountName, 'subscriptionStatus': accountStatus, 'supportgroup': "NONE", 'resourcecontact': "NONE", 'environment': "NONE", 'applicationservicenumber': "NONE", 'bac': "NONE", 'sbg': "NONE", 'sbu': "NONE", 'sbe': "NONE"})
        continue

    print(f"Querying tags for AWS account {account_id}...")
    # Set up the STS client and assume the hon_master_viewer role in the account.  STS not needed oon 980...420
    if account_id == "988390467345":
        print("Security account legacy which is in suspended")
        continue
    if account_id != "980840311420":
        sts = boto3.client('sts')
        role_arn = f"arn:aws:iam::{account_id}:role/hon_master_viewer"
        assumed_role = sts.assume_role(RoleArn=role_arn, RoleSessionName="AssumeRoleSession")
        # Use the assumed role credentials to set up a new boto3 client to access the account
        credentials = assumed_role['Credentials']
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
    # do not use sts for 980...420
    else:
        session = boto3.Session()

    accountCounter += 1
    print("Account Counter "+str(accountCounter))
    print("Account Name"+accountName)
    #Determine the effective tags we are targeting no region specification required
    supportgroup = "NONE"
    resourcecontact = "NONE"
    environment = "NONE"
    applicationservicenumber = "NONE"
    bac = "NONE"
    sbg = "NONE" 
    sbu = "NONE"
    sbe = "NONE" 
    client = session.client('organizations')
    response = client.describe_effective_policy(PolicyType='TAG_POLICY')
    policyContent = response.get('EffectivePolicy')
    policy_content = json.loads(policyContent["PolicyContent"])
    if "supportgroup" in policy_content["tags"]:
        supportgroup = policy_content["tags"]["supportgroup"]["tag_value"][0]
    if "resourcecontact" in policy_content["tags"]:
        resourcecontact = policy_content["tags"]["resourcecontact"]["tag_value"][0]
    if "environment" in policy_content["tags"]:
        environment = policy_content["tags"]["environment"]["tag_value"][0]
    if "applicationservicenumber" in policy_content["tags"]:
        applicationservicenumber = policy_content["tags"]["applicationservicenumber"]["tag_value"][0]
    if "bac" in policy_content["tags"]:
        bac = policy_content["tags"]["bac"]["tag_value"][0]
    if "sbg" in policy_content["tags"]:
        sbg = policy_content["tags"]["sbg"]["tag_value"][0]
    if "sbu" in policy_content["tags"]:
        sbu = policy_content["tags"]["sbu"]["tag_value"][0]
    if "sbe" in policy_content["tags"]:
        sbe = policy_content["tags"]["sbe"]["tag_value"][0]        
    listoftags = []
    if supportgroup is not None:
        supportgroupdict={"supportgroup": supportgroup}
        listoftags.append(supportgroupdict)
    if resourcecontact is not None:
        resourcecontactdict={"resourcecontact": resourcecontact}
        listoftags.append(resourcecontactdict)
    if environment is not None:
        environmentdict={"environment": environment}
        listoftags.append(environmentdict)
    if applicationservicenumber is not None:
        applicationservicenumberdict={"applicationservicenumber": applicationservicenumber}
        listoftags.append(applicationservicenumberdict)
    if bac is not None:
        bacdict={"bac": bac}
        listoftags.append(bacdict)
    if sbg is not None:
        sbgdict={"sbg": sbg}
        listoftags.append(sbgdict)
    if sbu is not None:
        sbudict={"sbu": sbu}
        listoftags.append(sbudict)
    if sbe is not None:
        sbedict={"sbe": sbe}
        listoftags.append(sbedict)              
    #print(supportgroupdict)
    #print(resourcecontactdict)
    #print(environmentdict)
    #print(applicationservicenumberdict)
    #print(bacdict)
    #print(sbgdict)
    #print(listoftags)
    with open(filename, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        # Write the rows of data to the CSV file
        #writer.writerow({'source': "AWS", 'exportDate': exportDate, 'subscriptionId': accountID, 'subscriptionName': accountName, 'tagsSBG': accountSBG, 'id': resourceID, 'awsRegion': awsRegion, 'type': resourceType})
        writer.writerow({'source': "AWS", 'exportDate': exportDate, 'subscriptionId': account_id, 'subscriptionName': accountName, 'subscriptionStatus': accountStatus, 'supportgroup': supportgroup, 'resourcecontact': resourcecontact, 'environment': environment, 'applicationservicenumber': applicationservicenumber, 'bac': bac, 'sbg': sbg, 'sbu': sbu, 'sbe': sbe})

# Creating Email to be sent to Cloud Team
msg = EmailMessage()
msg["From"] = "Rakshith.M@Honeywell.com"
msg["Subject"] = "AWS Effective Tag Inheritance Audit"
msg["To"] = "Rakshith.M@Honeywell.com"
msg.set_content("The following is an attachment of the AWS Effective Tag Inhertiance Model per Account.  Use this to identify where we are missing a mandatory tag at the AWS Organizations Tag Polilcy level which will be used for tag automation - GitHubAction")
msg.add_attachment(open(filename, "r").read(), filename=file_name_for_attachment)

#smtp.honeywell.com is 10.195.20.55
s = smtplib.SMTP('smtp.honeywell.com', 25)
s.send_message(msg)

# ## Azure Credentials
# tenantid = environ.get('AZURE_TENANT_ID')
# clientid = environ.get('AZURE_CLIENT_ID_PROD')
# secretid = environ.get('AZURE_CLIENT_SECRET_PROD')
# subscriptionid = '29a367f0-8487-43c0-bddb-383e60cf0e31'
# account_url = "https://cloudobservabilitysa.blob.core.windows.net"
# # container_url = "https://powerbistorageintern01.blob.core.windows.net/defaultasntags"
# container_name = "defaultasntags"

# Create boto client
def activateAwsClient(clientType, id, key, token=None, region='us-east-1'):
    # setup retries for boto3 clients, override default 'legacy' option and use new 'standard'
    config = Config(
        retries={
            'max_attempts': 10,
            'mode': 'standard'
        },
        region_name = region
    )
    # Create session using modified configs
    session = b3session(aws_access_key_id=id,
                        aws_secret_access_key=key,
                        aws_session_token=token)
    # Create the client using new session
    client = session.client(clientType, config=config)
    return client

# def activateAzureClient(tenantid, clientid, clientsecret):
#     credential = ClientSecretCredential(tenantid, clientid, clientsecret)
#     return credential

# # Upload File to Azure Storage Account as Blob
# credentials = activateAzureClient(tenantid=tenantid, clientid=clientid, clientsecret=secretid)
# storageaccountclient = BlobServiceClient(account_url=account_url, credential=credentials)
# containerclient = storageaccountclient.get_container_client(container=container_name)
# blobclient = containerclient.get_blob_client(blob=f"{filename}")

# with open(f"{filename}", 'rb') as f:
#     blobclient.upload_blob(data=f, overwrite=True)

print("Done")
     
    # Write headers
   