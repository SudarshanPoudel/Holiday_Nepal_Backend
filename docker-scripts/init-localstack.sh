#!/bin/bash
echo "Creating S3 bucket: holidaynepal"
awslocal s3api create-bucket --bucket holidaynepal
