#!/usr/bin/env python3

from src.python.aws_processor import AwsProcessor
import os

def main():
    try:
        # Read accounts
        accounts = AwsProcessor.read_accounts_list('config/accounts.list')

        # Base role ARN with placeholder
        base_assume_role_arn = "arn:aws:iam::ACCOUNT_ID:role/cross-account-role"

        # Process accounts sequentially
        AwsProcessor.process_accounts(
            accounts,
            "list",
            base_assume_role_arn,
            os.environ['WORKSPACE']
        )
    except Exception as e:
        print(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
