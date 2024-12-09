import sys
import json
import os
import boto3
from aws_utils.ec2_management import (
    list_instances_with_choice, create_instance, start_instance,
    stop_instance, reboot_instance, delete_instance, update_instance_name,
    available_zones, available_regions
)
from aws_utils.monitoring import get_cpu_usage
from aws_utils.ssh_utils import ssh_to_instance, execute_condor_status_on_instances
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def load_credentials():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(script_dir, "credentials.json")
        with open(credentials_path, 'r') as file:
            credentials = json.load(file)
        aws_access_key_id = credentials.get('aws_access_key_id')
        aws_secret_access_key = credentials.get('aws_secret_access_key')
        region = credentials.get('region', 'ap-northeast-2')  # Default region

        if not aws_access_key_id or not aws_secret_access_key:
            raise KeyError("AWS access key or secret key is missing in credentials.json.")

        return aws_access_key_id, aws_secret_access_key, region
    except FileNotFoundError:
        print(f"Error: credentials.json file not found in {script_dir}.")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing key {str(e)} in credentials.json.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in credentials.json.")
        sys.exit(1)

def init():
    aws_access_key_id, aws_secret_access_key, region = load_credentials()
    try:
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )
        ec2 = session.client('ec2')
        cloudwatch = session.client('cloudwatch')
        return ec2, cloudwatch
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    ec2, cloudwatch = init()

    while True:
        print("\n------------------------------------------------------------")
        print("           Amazon AWS Control Panel using SDK               ")
        print("------------------------------------------------------------")
        print("  EC2 Management:")
        print("  1. List instances              2. Create instance          ")
        print("  3. Start instance              4. Stop instance            ")
        print("  5. Reboot instance             6. Delete instance          ")
        print("  7. Update name tag                                        ")
        print("  8. Available zones             9. Available regions        ")
        print("  Monitoring:")
        print("  10. View CPU usage                                        ")
        print("  SSH and Custom Commands:")
        print("  11. SSH to instance             12. Execute condor_status  ")
        print("                                  99. Quit                   ")
        print("------------------------------------------------------------")
        
        choice = input("Enter an integer: ")
        if not choice.isdigit():
            print("Invalid input! Please enter a valid integer.")
            continue

        choice = int(choice)
        if choice == 1:
            list_instances_with_choice(ec2)
        elif choice == 2:
            create_instance(ec2)
        elif choice == 3:
            start_instance(ec2)
        elif choice == 4:
            stop_instance(ec2)
        elif choice == 5:
            reboot_instance(ec2)
        elif choice == 6:
            delete_instance(ec2)
        elif choice == 7:
            update_instance_name(ec2)
        elif choice == 8:
            available_zones(ec2)
        elif choice == 9:
            available_regions(ec2)
        elif choice == 10:
            get_cpu_usage(ec2, cloudwatch)
        elif choice == 11:
            ssh_to_instance(ec2)
        elif choice == 12:
            execute_condor_status_on_instances(ec2)
        elif choice == 99:
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    main()
