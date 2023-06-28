MAPT (Micro-Archive Publication Tool)
=====================================

This is a proof-of-concept for an application capable of publishing
a "micro-archive" as a bare-bones website. A micro-archive here is
basically a set of photographs or document scans in some folder
structure. The output is a website published on AWS Cloudfront that
includes a IIIF Viewer for browsing the images, and the generation of
EAD 2002 (XML) metadata.

This app, as it currently stands, also requires a fair bit of configuration
and additional infrastructure, namely:

 - an AWS S3 bucket, accessible to the app, where the image collections are
   located
 - a IIIF image server (e.g. Cantaloupe) that can also access the source
   images

There is a fair bit of configuration needed so the Streamlit secrets TOML file
looks something like this:

    [s3_credentials]
    access_key = "..." # The AWS access key
    secret_key = "..." # The AWS secret 
    region = "..."     # e.g. eu-west-1
    bucket = "..."     # The AWS S3 bucket name

    [iiif]
    server_url = "https://www.example.com/iiif/3/" # replace with actual IIIF URL

    [datasets]

    # Dataset key should be an AWS S3 prefix to the source data
    # including a trailing '/'
    [datasets."collection-1/"]
    name = "Collection 1"
    format = ".jpg"

    [datasets."collection-2/"]
    name = "Collection 2"
    format = ".png"

To work correctly the AWS permissions need to be set up so that in addition to 
having read access to the files on S3, the IAM user can also create Cloudfront
distributions.
