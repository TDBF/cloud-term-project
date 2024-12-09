import os
import json
import sys

def load_credentials():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(script_dir, "../credentials.json")
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
