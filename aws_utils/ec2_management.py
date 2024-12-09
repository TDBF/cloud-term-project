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
