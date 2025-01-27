import subprocess

class AwsProcessor:
    @staticmethod
    def read_accounts_list(accounts_file):
        accounts = []
        with open(accounts_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    accounts.append(line)

        print(f"Available AWS Accounts:\n{accounts}")
        return accounts

    @staticmethod
    def construct_role_arn(account_id, base_role_arn):
        return base_role_arn.replace("ACCOUNT_ID", account_id)

    @staticmethod
    def run_aws_command(action, assume_role_arn, workspace):
        cmd = [
            f"{workspace}/src/aws_runner.sh",
            "--action", action,
            "--assume_arn", assume_role_arn
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                text=True,
                capture_output=True
            )
            print(f"AWS Command Output:\n{result.stdout}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running AWS command: {e}")
            raise

    @staticmethod
    def process_accounts(account_list, action, base_assume_role_arn, workspace):
        if not account_list:
            print("No accounts detected to process")
            return

        for account_id in account_list:
            try:
                print(f"Processing Account ID: {account_id}")
                assume_role_arn = AwsProcessor.construct_role_arn(
                    account_id,
                    base_assume_role_arn
                )
                AwsProcessor.run_aws_command(action, assume_role_arn, workspace)
            except Exception as e:
                print(f"Failed to process account {account_id}: {e}")
                raise
