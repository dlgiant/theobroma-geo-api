#!/bin/bash

echo "🔍 Finding ECS service endpoint..."

# Check if AWS CLI is working
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured or not working"
    exit 1
fi

REGION="us-east-2"
CLUSTER="theobroma-production"
SERVICE="theobroma-geo-api-service"

echo "Checking ECS cluster: $CLUSTER"
aws ecs describe-clusters --clusters $CLUSTER --region $REGION --query 'clusters[0].status' --output text

echo "Checking ECS service: $SERVICE"
SERVICE_STATUS=$(aws ecs describe-services --cluster $CLUSTER --services $SERVICE --region $REGION --query 'services[0].status' --output text 2>/dev/null)

if [ "$SERVICE_STATUS" = "ACTIVE" ]; then
    echo "✅ Service is active"
    
    # Get task ARN
    TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER --service-name $SERVICE --region $REGION --query 'taskArns[0]' --output text)
    
    if [ "$TASK_ARN" != "None" ] && [ "$TASK_ARN" != "null" ]; then
        echo "📋 Task ARN: $TASK_ARN"
        
        # Get task details including network interface
        ENI_ID=$(aws ecs describe-tasks --cluster $CLUSTER --tasks $TASK_ARN --region $REGION --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
        
        if [ "$ENI_ID" != "None" ] && [ "$ENI_ID" != "null" ]; then
            echo "🌐 Network Interface: $ENI_ID"
            
            # Get public IP
            PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --region $REGION --query 'NetworkInterfaces[0].Association.PublicIp' --output text)
            
            if [ "$PUBLIC_IP" != "None" ] && [ "$PUBLIC_IP" != "null" ]; then
                echo "🎯 Public IP: $PUBLIC_IP"
                echo "🚀 Try accessing: http://$PUBLIC_IP:8000/health"
                
                # Test the endpoint
                echo "🔍 Testing endpoint..."
                if curl -f -s "http://$PUBLIC_IP:8000/health" >/dev/null; then
                    echo "✅ Service is accessible!"
                    curl -s "http://$PUBLIC_IP:8000/health" | jq .
                else
                    echo "❌ Service is not responding"
                fi
            else
                echo "❌ No public IP found"
            fi
        else
            echo "❌ No network interface found"
        fi
    else
        echo "❌ No running tasks found"
    fi
else
    echo "❌ Service not found or not active: $SERVICE_STATUS"
    echo "Available services:"
    aws ecs list-services --cluster $CLUSTER --region $REGION --query 'serviceArns' --output table
fi
