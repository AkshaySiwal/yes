#!/bin/bash

function get_cli_options() {
    while getopts ":a:r:" opt; do
        case ${opt} in
            a )
                ACTION=$OPTARG
                ;;
            r )
                ASSUME_ARN=$OPTARG
                ;;
            \? )
                echo "Invalid Option: -$OPTARG" 1>&2
                exit 1
                ;;
            : )
                echo "Invalid Option: -$OPTARG requires an argument" 1>&2
                exit 1
                ;;
        esac
    done
}

function list_s3() {
    echo "Listing S3 buckets for assumed role..."
    aws s3 ls
}

function main() {
    get_cli_options "$@"
    
    SESSIONNAME="AWS-S3-List-${BUILD_NUMBER}"
    
    echo "Assuming role: ${ASSUME_ARN}"
    eval $(aws sts assume-role \
        --output json \
        --role-arn "${ASSUME_ARN}" \
        --role-session-name "${SESSIONNAME}" \
        | jq -r '.Credentials | @sh "export AWS_SESSION_TOKEN=\(.SessionToken) \
        export AWS_ACCESS_KEY_ID=\(.AccessKeyId) \
        export AWS_SECRET_ACCESS_KEY=\(.SecretAccessKey)"')
    
    aws sts get-caller-identity
    list_s3
}

main "$@"
