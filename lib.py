import datetime
import os

import boto3
import streamlit as st
from botocore.exceptions import ClientError

from ead import SimpleEad, EadItem

TITLE = "title"
DATE_DESC = "datedesc"
EXTENT = "extent"
BIOG_HIST = "bioghist"
SCOPE = "scope"
LANGS = "langs"
HOLDER = "holder"
STREET = "street"
POSTCODE = "postcode"


def value_or_default(key: str, default):
    return st.session_state[key] if key in st.session_state else default


def create_presigned_url(s3, object_name, expiration=3600):
    bucket_name = st.secrets.s3_credentials.bucket
    # Generate a presigned URL for the S3 object
    try:
        response = s3.generate_presigned_url('get_object',
                                             Params={'Bucket': bucket_name,
                                                     'Key': object_name},
                                             ExpiresIn=expiration)
    except ClientError as e:
        st.error(e)
        return None

    # The response contains the presigned URL
    return response


@st.experimental_memo
def load_files():
    s3 = boto3.client('s3',
                      region_name=st.secrets.s3_credentials.region,
                      aws_access_key_id=st.secrets.s3_credentials.access_key,
                      aws_secret_access_key=st.secrets.s3_credentials.secret_key,
                      )

    r = s3.list_objects_v2(
        Bucket=st.secrets.s3_credentials.bucket,
        Prefix=st.secrets.s3_credentials.prefix)
    file_meta = [meta for meta in r["Contents"] if not meta["Key"].endswith("/")]
    items = []
    for i, meta in enumerate(file_meta):
        key = meta["Key"]
        item_id = os.path.basename(os.path.splitext(key)[0])
        url = create_presigned_url(s3, key)
        items.append((item_id, url))
    return items


def init_page():
    if "items" not in st.session_state:
        st.session_state.items = load_files()

    st.write("# WP11 Microarchives Test")

    if st.button("Show State"):
        st.write(st.session_state)
