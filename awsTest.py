import boto3
import json
import sys
import os
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
            credentials.get('region', 'ap-northeast-2'), 
            credentials.get('default_ami_id')
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
    aws_access_key_id, aws_secret_access_key, region, _ = load_credentials()
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

# List EC2 Instances
def list_instances(ec2):
    print("Listing instances...")
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
                print(f"[ID] {instance['InstanceId']}, [Name] {name}, [AMI] {instance['ImageId']}, "
                      f"[Type] {instance['InstanceType']}, [State] {instance['State']['Name']}, "
                      f"[Monitoring State] {instance['Monitoring']['State']}")
    except Exception as e:
        print(f"Error listing instances: {str(e)}")

# List EC2 Instances with numbered choices
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
                instances.append({
                    'InstanceId': instance['InstanceId'],
                    'Name': name,
                    'State': instance['State']['Name']
                })
        if instances:
            for idx, inst in enumerate(instances, 1):
                print(f"{idx}. [ID] {inst['InstanceId']}, [Name] {inst['Name']}, [State] {inst['State']}")
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

# List Availability Zones
def available_zones(ec2):
    print("Available zones...")
    try:
        response = ec2.describe_availability_zones()
        for zone in response['AvailabilityZones']:
            print(f"[ID] {zone['ZoneId']}, [Region] {zone['RegionName']}, [Zone] {zone['ZoneName']}")
        print(f"You have access to {len(response['AvailabilityZones'])} Availability Zones.")
    except Exception as e:
        print(f"Error listing availability zones: {str(e)}")

# List Available Regions
def available_regions(ec2):
    print("Available regions...")
    try:
        response = ec2.describe_regions()
        for region in response['Regions']:
            print(f"[Region] {region['RegionName']}, [Endpoint] {region['Endpoint']}")
    except Exception as e:
        print(f"Error listing regions: {str(e)}")

# Start EC2 Instance
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

# Stop EC2 Instance
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

# Create EC2 Instance
def create_instance(ec2):
    _, _, _, ami_id = load_credentials()
    if not ami_id:
        print("Error: No default AMI ID found in credentials.json.")
        return
    
    print(f"Creating instance with AMI {ami_id}...")
    try:
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1
        )
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Successfully created instance {instance_id} with AMI {ami_id}.")
    except Exception as e:
        print(f"Error creating instance: {str(e)}")

# Reboot EC2 Instance
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

# List Images
def list_images(ec2, image_name):
    print("Listing images...")
    try:
        response = ec2.describe_images(Filters=[{'Name': 'name', 'Values': [image_name]}])
        for image in response['Images']:
            print(f"[ImageID] {image['ImageId']}, [Name] {image['Name']}, [Owner] {image['OwnerId']}")
    except Exception as e:
        print(f"Error listing images: {str(e)}")

# Terminate EC2 Instance
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

# Main menu
def main():
    ec2 = init()

    while True:
        print("\n------------------------------------------------------------")
        print("           Amazon AWS Control Panel using SDK               ")
        print("------------------------------------------------------------")
        print("  1. List instances              2. Available zones         ")
        print("  3. Start instance              4. Available regions       ")
        print("  5. Stop instance               6. Create instance         ")
        print("  7. Reboot instance             8. List images             ")
        print("  9. Delete instance                                          ")
        print("                                99. Quit                    ")
        print("------------------------------------------------------------")
        
        choice = input("Enter an integer: ")
        if not choice.isdigit():
            print("Invalid input! Please enter a valid integer.")
            continue

        choice = int(choice)
        if choice == 1:
            list_instances(ec2)
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
        elif choice == 99:
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    main()
