import os
import logging
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# DigitalOcean Spaces configuration
region = os.getenv('DO_SPACE_REGION')
endpoint = os.getenv('DO_SPACE_ENDPOINT')
key = os.getenv('DO_SPACE_KEY')
secret = os.getenv('DO_SPACE_SECRET')
bucket_name = os.getenv('DO_SPACE_BUCKET')

# Create a session using DigitalOcean Spaces credentials
session = boto3.session.Session()
client = session.client('s3',
                        region_name=region,
                        endpoint_url=endpoint,
                        aws_access_key_id=key,
                        aws_secret_access_key=secret)

def upload_file(file_path, object_name=None):
    """Upload a file to DigitalOcean Spaces bucket"""
    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        client.upload_file(file_path, bucket_name, object_name)
    except ClientError as e:
        logging.error(f"Error uploading file {file_path}: {e}")
        return False
    return True

def main():
    transcripts_dir = 'transcripts'
    
    if not os.path.exists(transcripts_dir):
        logging.error(f"Directory '{transcripts_dir}' does not exist.")
        return

    for filename in os.listdir(transcripts_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(transcripts_dir, filename)
            logging.info(f"Uploading {filename} to DigitalOcean Spaces...")
            if upload_file(file_path, f"koopcast_transcripts/{filename}"):
                logging.info(f"Successfully uploaded {filename}")
            else:
                logging.warning(f"Failed to upload {filename}")

    logging.info("Upload process completed.")

if __name__ == '__main__':
    main()