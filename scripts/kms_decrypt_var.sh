#!/bin/sh
set -e
##
# This script decrypts an environment variable
# Inputs:
# AWS_KMS_REGION
# AWS_KMS_ALIAS
#
# Positional arguments:
# $1 - variable value to decrypt
##

echo $1 | base64 -d > tmp_decrypt_file
aws kms decrypt --region ${AWS_KMS_REGION} \
    --key-id "${AWS_KMS_ALIAS}" \
    --query Plaintext \
    --ciphertext-blob fileb://tmp_decrypt_file | tr -d '"'
rm tmp_decrypt_file