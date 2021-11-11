import re
import os
import google.auth
from google.auth.transport import requests
from google.auth import compute_engine
from google.cloud import storage
from datetime import datetime, timedelta
import json
import logging
import urllib3
from urllib.parse import urlencode

def process_name(key):
    key = key.replace('.csv', '').split('/')[-1]
    file_regexp = os.getenv('FILE_REGEXP', None)
    if not file_regexp:
        return key
    m = re.search(file_regexp, key)
    return m.group(0) if m is not None else key

def create_presigned_url(bucket_name, object_name, expiration=3600):
    credentials, project_id = google.auth.default()

    # Perform a refresh request to get the access token of the current credentials (Else, it's None)
    r = requests.Request()
    credentials.refresh(r)

    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(object_name)
    expires = datetime.now() + timedelta(seconds=86400)

    # In case of user credential use, define manually the service account to use (for development purpose only)
    service_account_email = "YOUR DEV SERVICE ACCOUNT"
    # If you use a service account credential, you can use the embedded email
    if hasattr(credentials, "service_account_email"):
        service_account_email = credentials.service_account_email

    url = blob.generate_signed_url(expiration=expires,service_account_email=service_account_email, access_token=credentials.token)
    return url

def upload_to_tinybird(csv_path, name):
    http = urllib3.PoolManager()
    fields = {
        'mode': 'append',
        'name': name.replace('.csv',''),
        'url': csv_path
    }
    headers={
        'Authorization': 'Bearer ' + os.environ['TB_TOKEN']
    }
    # Tinybird datasource url
    url = f"{ os.getenv('TB_HOST', 'https://api.tinybird.co') }/v0/datasources?"    
    print(url + urlencode(fields))
    return http.request('POST', url + urlencode(fields), headers=headers)

def ingest_to_tinybird(event, context):
    """Background Cloud Function to be triggered by Cloud Storage.
       This generic function logs relevant data when a file is changed.

    Args:
        event (dict):  The dictionary with data specific to this type of event.
                       The `data` field contains a description of the event in
                       the Cloud Storage `object` format described here:
                       https://cloud.google.com/storage/docs/json_api/v1/objects#resource
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    bucket = event['bucket']
    key = event['name']
    csv_path = create_presigned_url(bucket, key)
    name = process_name(key)
    r = upload_to_tinybird(csv_path, name=name)
    status = r.status
    response = {
        'status': status,
        'name': name,
        'bucket': bucket,
        'tb_data': r.data.decode('utf-8')
    }

    print(json.dumps(response))
