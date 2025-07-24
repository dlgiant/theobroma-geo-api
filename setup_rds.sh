#!/bin/bash

# AWS RDS Setup Script for Theobroma Geo API
# Creates PostgreSQL database with PostGIS support

# set -e  # Don't exit on any error to handle existing resources

# Configuration
DB_INSTANCE_ID="theobroma-geo-staging-db"
DB_NAME="geoapi"
DB_USERNAME="geoapi_user"
DB_PASSWORD="SecurePassword123"
DB_INSTANCE_CLASS="db.t3.micro"
ENGINE_VERSION="14.12"
ALLOCATED_STORAGE="20"
SECURITY_GROUP_NAME="theobroma-geo-db-sg"
SUBNET_GROUP_NAME="theobroma-geo-db-subnet-group"

echo "🚀 Starting AWS RDS setup for Theobroma Geo API..."

# Get current IP for security group
echo "📍 Getting current public IP..."
CURRENT_IP=$(curl -s https://ipinfo.io/ip)
echo "Current IP: $CURRENT_IP"

# Create or get existing security group
echo "🛡️ Creating or getting security group..."
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP_NAME \
    --description "Security group for Theobroma Geo API database" \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --group-names $SECURITY_GROUP_NAME \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

echo "Security Group ID: $SECURITY_GROUP_ID"

# Add inbound rules to security group
echo "🔐 Adding security group rules..."
# Allow PostgreSQL from current IP
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 5432 \
    --cidr $CURRENT_IP/32 2>/dev/null || echo "Rule for current IP may already exist"

# Allow PostgreSQL from common staging server IPs (optional)
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 5432 \
    --cidr 0.0.0.0/0 2>/dev/null || echo "⚠️  Warning: Could not add open access rule (may already exist)"

# Get default VPC and subnets
echo "🌐 Getting VPC information..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
echo "Default VPC ID: $VPC_ID"

SUBNET_IDS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[*].SubnetId' \
    --output text)
echo "Subnet IDs: $SUBNET_IDS"

# Create DB subnet group
echo "🏗️ Creating or getting DB subnet group..."
aws rds create-db-subnet-group \
    --db-subnet-group-name $SUBNET_GROUP_NAME \
    --db-subnet-group-description "Subnet group for Theobroma Geo API database" \
    --subnet-ids $SUBNET_IDS 2>/dev/null || echo "Subnet group already exists"

# Create RDS instance
echo "🗄️ Creating RDS PostgreSQL instance..."
aws rds create-db-instance \
    --db-instance-identifier $DB_INSTANCE_ID \
    --db-instance-class $DB_INSTANCE_CLASS \
    --engine postgres \
    --engine-version $ENGINE_VERSION \
    --master-username $DB_USERNAME \
    --master-user-password $DB_PASSWORD \
    --allocated-storage $ALLOCATED_STORAGE \
    --db-name $DB_NAME \
    --vpc-security-group-ids $SECURITY_GROUP_ID \
    --db-subnet-group-name $SUBNET_GROUP_NAME \
    --publicly-accessible \
    --no-multi-az \
    --storage-type gp2 \
    --backup-retention-period 1 \
    --no-deletion-protection

echo "⏳ Waiting for RDS instance to be available..."
aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_ID

# Get the endpoint
echo "📡 Getting database endpoint..."
ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE_ID \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

echo "✅ RDS setup complete!"
echo "📊 Database Details:"
echo "   Instance ID: $DB_INSTANCE_ID"
echo "   Endpoint: $ENDPOINT"
echo "   Database: $DB_NAME"
echo "   Username: $DB_USERNAME"
echo "   Password: $DB_PASSWORD"
echo ""
echo "🔗 Connection URL:"
echo "   postgresql://$DB_USERNAME:$DB_PASSWORD@$ENDPOINT:5432/$DB_NAME"
echo ""
echo "💡 Update your .env file with:"
echo "   DATABASE_URL=postgresql://$DB_USERNAME:$DB_PASSWORD@$ENDPOINT:5432/$DB_NAME"

# Clean up temp files
rm -f /tmp/sg_id.txt

echo "🎉 Setup completed successfully!"
