import boto3
import json
import sys
import os
import subprocess
import paramiko
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Load AWS credentials from a file
def load_credentials():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(script_dir, "credentials.json")
        with open(credentials_path, 'r') as file:
            credentials = json.load(file)
        return (
            credentials['aws_access_key_id'], 
            credentials['aws_secret_access_key'], 
            credentials.get('region', 'ap-northeast-2')
        )
    except FileNotFoundError:
        print(f"Error: Credentials file not found.")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing key {str(e)} in credentials file.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in credentials file.")
        sys.exit(1)

# AWS Session Initialization
def init():
    aws_access_key_id, aws_secret_access_key, region = load_credentials()
    try:
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )
        ec2 = session.client('ec2')
        return ec2
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

# List EC2 Instances with detailed information
def list_instances_with_choice(ec2):
    print("Listing instances...")
    instances = []
    try:
        response = ec2.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                name = "N/A"
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                instance_details = {
                    'InstanceId': instance['InstanceId'],
                    'Name': name,
                    'State': instance['State']['Name'],
                    'Type': instance.get('InstanceType', 'N/A'),
                    'PublicIP': instance.get('PublicIpAddress', 'N/A'),
                    'PrivateIP': instance.get('PrivateIpAddress', 'N/A'),
                    'Zone': instance['Placement']['AvailabilityZone']
                }
                instances.append(instance_details)
        
        if instances:
            print(f"{'No.':<5}{'Instance ID':<20}{'Name':<20}{'State':<15}{'Type':<15}{'Public IP':<20}{'Private IP':<15}{'Zone'}")
            print("-" * 115)
            for idx, inst in enumerate(instances, 1):
                print(f"{idx:<5}{inst['InstanceId']:<20}{inst['Name']:<20}{inst['State']:<15}{inst['Type']:<15}{inst['PublicIP']:<20}{inst['PrivateIP']:<15}{inst['Zone']}")
            return instances
        else:
            print("No instances found.")
            return None
    except Exception as e:
        print(f"Error listing instances: {str(e)}")
        return None

# Select an instance by number
def select_instance(instances):
    if not instances:
        print("No instances to select.")
        return None
    try:
        choice = int(input("Select an instance by number: "))
        if 1 <= choice <= len(instances):
            return instances[choice - 1]['InstanceId']
        else:
            print("Invalid selection.")
            return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None

# List available AMIs and let user select one
def list_and_select_ami(ec2):
    try:
        print("Fetching available AMIs...")
        response = ec2.describe_images(Owners=['self'])
        amis = [
            {'ImageId': image['ImageId'], 'Name': image.get('Name', 'N/A')}
            for image in response['Images']
        ]
        if not amis:
            print("No AMIs found.")
            return None

        for idx, ami in enumerate(amis, 1):
            print(f"{idx}. [ImageId] {ami['ImageId']}, [Name] {ami['Name']}")
        
        while True:
            try:
                choice = int(input("Select an AMI by number: "))
                if 1 <= choice <= len(amis):
                    return amis[choice - 1]['ImageId']
                else:
                    print("Invalid choice. Please select a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"Error listing AMIs: {str(e)}")
        return None

# Create a new EC2 instance with a specified security group
def create_instance(ec2):
    ami_id = list_and_select_ami(ec2)
    if not ami_id:
        print("No AMI selected. Instance creation canceled.")
        return

    instance_name = input("Enter a name for the instance: ").strip()
    if not instance_name:
        print("Invalid instance name. Operation canceled.")
        return

    # 지정할 보안 그룹 ID
    security_group_id = "sg-0d9d4b03a4fe1cd2b"

    try:
        print(f"Creating an instance with security group {security_group_id}...")
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[security_group_id],  # 보안 그룹 설정
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': instance_name}]
            }]
        )
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Successfully created instance {instance_id} with name '{instance_name}'.")
    except Exception as e:
        print(f"Error creating instance: {str(e)}")


# Update the name tag of an EC2 instance
def update_instance_name(ec2):
    instances = list_instances_with_choice(ec2)
    if instances:
        instance_id = select_instance(instances)
        if instance_id:
            new_name = input(f"Enter the new name for instance {instance_id}: ").strip()
            if new_name:
                print(f"Updating name tag of instance {instance_id} to '{new_name}'...")
                try:
                    ec2.create_tags(
                        Resources=[instance_id],
                        Tags=[{'Key': 'Name', 'Value': new_name}]
                    )
                    print(f"Successfully updated instance {instance_id} with new name '{new_name}'.")
                except Exception as e:
                    print(f"Error updating name tag for instance {instance_id}: {str(e)}")
            else:
                print("Invalid name. No changes made.")

# Supporting functions for existing functionalities
def available_zones(ec2):
    print("Available zones...")
    try:
        response = ec2.describe_availability_zones()
        for zone in response['AvailabilityZones']:
            print(f"[ID] {zone['ZoneId']}, [Region] {zone['RegionName']}, [Zone] {zone['ZoneName']}")
    except Exception as e:
        print(f"Error listing availability zones: {str(e)}")

def available_regions(ec2):
    print("Available regions...")
    try:
        response = ec2.describe_regions()
        for region in response['Regions']:
            print(f"[Region] {region['RegionName']}, [Endpoint] {region['Endpoint']}")
    except Exception as e:
        print(f"Error listing regions: {str(e)}")

def start_instance(ec2):
    instances = list_instances_with_choice(ec2)
    if instances:
        instance_id = select_instance(instances)
        if instance_id:
            print(f"Starting instance {instance_id}...")
            try:
                ec2.start_instances(InstanceIds=[instance_id])
                print(f"Successfully started instance {instance_id}.")
            except Exception as e:
                print(f"Error starting instance {instance_id}: {str(e)}")

def stop_instance(ec2):
    instances = list_instances_with_choice(ec2)
    if instances:
        instance_id = select_instance(instances)
        if instance_id:
            print(f"Stopping instance {instance_id}...")
            try:
                ec2.stop_instances(InstanceIds=[instance_id])
                print(f"Successfully stopped instance {instance_id}.")
            except Exception as e:
                print(f"Error stopping instance {instance_id}: {str(e)}")

def reboot_instance(ec2):
    instances = list_instances_with_choice(ec2)
    if instances:
        instance_id = select_instance(instances)
        if instance_id:
            print(f"Rebooting instance {instance_id}...")
            try:
                ec2.reboot_instances(InstanceIds=[instance_id])
                print(f"Successfully rebooted instance {instance_id}.")
            except Exception as e:
                print(f"Error rebooting instance {instance_id}: {str(e)}")

def list_images(ec2):
    print("Listing all images...")
    try:
        response = ec2.describe_images(Owners=['self'])
        if not response['Images']:
            print("No images found.")
            return

        for image in response['Images']:
            print(f"[ImageID] {image['ImageId']}, [Name] {image.get('Name', 'N/A')}, [Owner] {image['OwnerId']}")
    except Exception as e:
        print(f"Error listing images: {str(e)}")

def delete_instance(ec2):
    instances = list_instances_with_choice(ec2)
    if instances:
        instance_id = select_instance(instances)
        if instance_id:
            print(f"Terminating instance {instance_id}...")
            try:
                ec2.terminate_instances(InstanceIds=[instance_id])
                print(f"Successfully terminated instance {instance_id}.")
            except Exception as e:
                print(f"Error terminating instance {instance_id}: {str(e)}")


# SSH access to an instance
def ssh_to_instance(ec2):
    instances = list_instances_with_choice(ec2)
    if not instances:
        print("No instances available for SSH access.")
        return

    instance_id = select_instance(instances)
    if not instance_id:
        print("No instance selected. Operation canceled.")
        return

    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        public_ip = instance.get('PublicIpAddress')

        if not public_ip:
            print(f"Instance {instance_id} does not have a public IP address.")
            return

        print(f"Selected instance {instance_id} with public IP: {public_ip}")
        key_path = input("Enter the path to your private key file (.pem): ").strip()
        if not os.path.exists(key_path):
            print(f"Key file {key_path} does not exist.")
            return

        ssh_command = f"ssh -i {key_path} ec2-user@{public_ip}"
        print(f"To SSH into the instance, the following command will be executed:")
        print(ssh_command)
        
        run_ssh = input("Do you want to execute this SSH command now? (y/n): ").strip().lower()
        if run_ssh == "y":
            try:
                subprocess.run(ssh_command, shell=True, check=True)
                print("SSH connection established successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error executing SSH command: {e}")
    except Exception as e:
        print(f"Error retrieving instance details: {str(e)}")


# Execute condor_status on selected instances
def execute_condor_status_on_instances(ec2):
    instances = list_instances_with_choice(ec2)
    if not instances:
        print("No instances available.")
        return

    instance_id = select_instance(instances)
    if not instance_id:
        print("No instance selected. Operation canceled.")
        return

    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        public_ip = instance.get('PublicIpAddress')

        if not public_ip:
            print(f"Instance {instance_id} does not have a public IP address.")
            return

        print(f"Selected instance {instance_id} with public IP: {public_ip}")
        key_path = input("Enter the path to your private key file (.pem): ").strip()
        if not os.path.exists(key_path):
            print(f"Key file {key_path} does not exist.")
            return

        # SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                hostname=public_ip,
                username="ec2-user",  # Update if using a different default username
                key_filename=key_path
            )
            print("Connected successfully. Executing condor_status...")
            
            # Execute condor_status
            stdin, stdout, stderr = ssh.exec_command("condor_status")
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if output:
                print("\nOutput of condor_status command:\n")
                print(output)
            if error:
                print("\nError output of condor_status command:\n")
                print(error)

        except paramiko.AuthenticationException:
            print("Authentication failed. Please check your private key and username.")
        except paramiko.SSHException as e:
            print(f"SSH connection error: {e}")
        finally:
            ssh.close()
    except Exception as e:
        print(f"Error retrieving instance details or executing command: {str(e)}")


# Main menu
def main():
    ec2 = init()

    while True:
        print("\n------------------------------------------------------------")
        print("           Amazon AWS Control Panel using SDK               ")
        print("------------------------------------------------------------")
        print("  1.  List instances              2.  Available zones        ")
        print("  3.  Start instance              4.  Available regions      ")
        print("  5.  Stop instance               6.  Create instance        ")
        print("  7.  Reboot instance             8.  List all images        ")
        print("  9.  Delete instance             10. Update name tag        ")
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
            available_zones(ec2)
        elif choice == 3:
            start_instance(ec2)
        elif choice == 4:
            available_regions(ec2)
        elif choice == 5:
            stop_instance(ec2)
        elif choice == 6:
            create_instance(ec2)
        elif choice == 7:
            reboot_instance(ec2)
        elif choice == 8:
            image_name = input("Enter image name filter: ").strip()
            list_images(ec2, image_name)
        elif choice == 9:
            delete_instance(ec2)
        elif choice == 10:
            update_instance_name(ec2)
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
