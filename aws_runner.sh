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
    aws s3 ls
}

function main() {
    # Get all cli inputs and validate variables
    get_cli_options "$@"
    
    echo "============================================"
    echo "==== Get STS for role assumption ===="
    echo "*** INFO: Getting AWS Token ***"
    
    SESSIONNAME="AWS-S3-List-Pipeline-${BUILD_NUMBER}"
    
    # Assume the AWS role and set credentials
    eval $(aws sts assume-role \
        --output json \
        --role-arn "${ASSUME_ARN}" \
        --role-session-name "${SESSIONNAME}" \
        | jq -r '.Credentials | @sh "export AWS_SESSION_TOKEN=\(.SessionToken) \
        export AWS_ACCESS_KEY_ID=\(.AccessKeyId) \
        export AWS_SECRET_ACCESS_KEY=\(.SecretAccessKey)"')
    
    # Verify the assumed role
    aws sts get-caller-identity
    
    # Execute S3 list
    list_s3
}

# Execute main function with all script arguments
main "$@"
