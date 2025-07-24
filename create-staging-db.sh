#!/bin/bash

# Theobroma Geo API - AWS RDS Staging Database Setup
# Creates PostgreSQL database with PostGIS extension on AWS RDS

set -e

# Configuration
REGION="us-east-2"
DB_INSTANCE_ID="theobroma-geo-db-staging"
DB_NAME="theobroma_geo_staging"
DB_USERNAME="theobroma_admin"
DB_PASSWORD="TheobromaGeo2024!"  # Change this to a secure password
DB_PORT=5432
SECURITY_GROUP_NAME="theobroma-geo-db-sg"

echo "🌱 Creating Theobroma Geo API Staging Database on AWS RDS..."

# Get current IP for security group
echo "📍 Getting current IP address..."
CURRENT_IP=$(curl -s https://ipinfo.io/ip)
echo "Current IP: $CURRENT_IP"

# Get default VPC ID
echo "🔍 Getting default VPC..."
VPC_ID=$(aws ec2 describe-vpcs --region $REGION --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
if [ "$VPC_ID" = "None" ] || [ -z "$VPC_ID" ]; then
    echo "❌ No default VPC found. Getting first available VPC..."
    VPC_ID=$(aws ec2 describe-vpcs --region $REGION --query 'Vpcs[0].VpcId' --output text)
fi
echo "Using VPC: $VPC_ID"

# Create security group
echo "🔒 Creating security group..."
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP_NAME \
    --description "Security group for Theobroma Geo API staging database" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" "Name=vpc-id,Values=$VPC_ID" \
    --region $REGION \
    --query 'SecurityGroups[0].GroupId' --output text)

echo "Security Group ID: $SECURITY_GROUP_ID"

# Add inbound rules for PostgreSQL
echo "🚪 Adding inbound rules..."

# Allow from current IP
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port $DB_PORT \
    --cidr $CURRENT_IP/32 \
    --region $REGION 2>/dev/null || echo "Rule for current IP already exists"

# Allow from common staging server IPs (you may need to adjust these)
# For staging.theobroma.digital - you'll need to get the actual IP
echo "🌐 Adding rule for staging server..."
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port $DB_PORT \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "Rule for staging server already exists"

# Get subnet group info
echo "🏗️  Getting subnet information..."
SUBNET_IDS=$(aws ec2 describe-subnets --region $REGION --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text)
SUBNET_ARRAY=($SUBNET_IDS)

# Create DB subnet group
echo "📡 Creating DB subnet group..."
aws rds create-db-subnet-group \
    --db-subnet-group-name "${DB_INSTANCE_ID}-subnet-group" \
    --db-subnet-group-description "Subnet group for $DB_INSTANCE_ID" \
    --subnet-ids ${SUBNET_ARRAY[@]} \
    --region $REGION 2>/dev/null || echo "Subnet group already exists"

# Create RDS instance
echo "🗄️  Creating RDS PostgreSQL instance..."
aws rds create-db-instance \
    --db-instance-identifier $DB_INSTANCE_ID \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version "14.12" \
    --master-username $DB_USERNAME \
    --master-user-password $DB_PASSWORD \
    --allocated-storage 20 \
    --storage-type gp2 \
    --vpc-security-group-ids $SECURITY_GROUP_ID \
    --db-subnet-group-name "${DB_INSTANCE_ID}-subnet-group" \
    --db-name $DB_NAME \
    --port $DB_PORT \
    --publicly-accessible \
    --no-auto-minor-version-upgrade \
    --backup-retention-period 7 \
    --region $REGION

echo "⏳ Database instance creation initiated. This may take 10-15 minutes..."
echo "📋 Database details:"
echo "   Instance ID: $DB_INSTANCE_ID"
echo "   Database Name: $DB_NAME"
echo "   Username: $DB_USERNAME"
echo "   Port: $DB_PORT"
echo "   Region: $REGION"

# Wait for instance to be available
echo "⏳ Waiting for database to become available..."
aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_ID --region $REGION

# Get the endpoint
echo "🔗 Getting database endpoint..."
DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE_ID \
    --region $REGION \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

echo "✅ Database created successfully!"
echo "📝 Connection details:"
echo "   Endpoint: $DB_ENDPOINT"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   Username: $DB_USERNAME"
echo "   Password: $DB_PASSWORD"
echo ""
echo "🔗 Connection string:"
echo "   postgresql://$DB_USERNAME:$DB_PASSWORD@$DB_ENDPOINT:$DB_PORT/$DB_NAME"
echo ""
echo "🚀 Next steps:"
echo "   1. Install PostGIS extension: CREATE EXTENSION postgis;"
echo "   2. Run the sample data script"
echo "   3. Update your application configuration"
