# GCS + cloud function -> Automatically ingesting to Tinybird from Google Cloud Storage

This repository contains a instructions to configure a Google Cloud function that is automatically triggered each time a new CSV file is uploaded to a given Google Cloud Storage bucket.

The Google Cloud function function appends the contents of the CSV file to a Tinybird Data Source.

## How to deploy the Cloud Function

Install the `gcloud` command line tool and run these commands:

```sh
# edit the .env.yaml file to set your Tinybird token available from https://ui.tinybird.co/tokens
cp .env.yaml.sample .env.yaml

# set some environment variables before deploying
PROJECT_NAME=<the_GCP_project_name>
SERVICE_ACCOUNT_NAME=<service_account_name@project_name.iam.gserviceaccount.com>
BUCKET_NAME=<bucket_name>
REGION=<region>
TB_FUNCTION_NAME=<name_of_the_function>

# grant permissions to deploy the cloud function and read from storage to the service account
gcloud projects add-iam-policy-binding $PROJECT_NAME --member serviceAccount:$SERVICE_ACCOUNT_NAME --role roles/storage.admin
gcloud projects add-iam-policy-binding $PROJECT_NAME --member serviceAccount:$SERVICE_ACCOUNT_NAME --role roles/iam.serviceAccountTokenCreator
gcloud projects add-iam-policy-binding $PROJECT_NAME --member serviceAccount:$SERVICE_ACCOUNT_NAME --role roles/editor

# deploy the cloud function
gcloud functions deploy $TB_FUNCTION_NAME \
--runtime python38 \
--trigger-resource $BUCKET_NAME \
--trigger-event google.storage.object.finalize \
--region $REGION \
--env-vars-file .env.yaml \
--service-account $SERVICE_ACCOUNT_NAME
```

Once finished, go to the Google Cloud console and check the cloud function is there and the `TB_HOST`, `TB_TOKEN`, and `FILE_REGEXP` variables required to run the script are available.

![](output.gif)
