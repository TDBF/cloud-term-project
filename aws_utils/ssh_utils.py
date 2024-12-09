import subprocess
import paramiko
import os
from aws_utils.ec2_management import list_instances_with_choice, select_instance

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
