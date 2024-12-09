from datetime import datetime, timedelta
from aws_utils.ec2_management import list_instances_with_choice, select_instance

def get_cpu_usage(ec2, cloudwatch):
    instances = list_instances_with_choice(ec2)
    if not instances:
        print("No instances available.")
        return

    instance_id = select_instance(instances)
    if not instance_id:
        print("No instance selected. Operation canceled.")
        return

    try:
        # Get CPU usage metrics from CloudWatch
        response = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'cpuUsage',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EC2',
                            'MetricName': 'CPUUtilization',
                            'Dimensions': [
                                {'Name': 'InstanceId', 'Value': instance_id}
                            ]
                        },
                        'Period': 300,  # 5 minutes
                        'Stat': 'Average'
                    },
                    'ReturnData': True
                }
            ],
            StartTime=datetime.utcnow() - timedelta(hours=1),  # Last 1 hour
            EndTime=datetime.utcnow()
        )

        print(f"CPU usage for instance {instance_id} in the last hour:")
        for result in response['MetricDataResults']:
            if result['Values']:
                for timestamp, value in zip(result['Timestamps'], result['Values']):
                    print(f"Time: {timestamp}, CPU Utilization: {value}%")
            else:
                print("No CPU usage data available for the selected instance.")
    except Exception as e:
        print(f"Error fetching CPU usage data: {str(e)}")
