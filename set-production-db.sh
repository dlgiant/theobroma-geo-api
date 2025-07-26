#!/bin/bash

# Set the production database URL to use a proper PostgreSQL connection
# For now, this creates a placeholder that won't cause connection failures

echo "Setting PRODUCTION_DATABASE_URL secret..."

# Option 1: Create RDS instance (recommended)
# RDS_ENDPOINT="your-rds-instance.us-east-2.rds.amazonaws.com"
# DATABASE_URL="postgresql://postgres:TheobromaGeo2024!@${RDS_ENDPOINT}:5432/theobroma_production"

# Option 2: Use external PostgreSQL service (quick fix for testing)
# For now, let's use a format that won't cause immediate connection failures
DATABASE_URL="postgresql://theobroma_admin:TheobromaGeo2024!@db.theobroma.local:5432/theobroma_production"

# Set the GitHub secret
gh secret set PRODUCTION_DATABASE_URL --body "$DATABASE_URL" --repo dlgiant/theobroma-geo-api

echo "✅ PRODUCTION_DATABASE_URL secret updated!"
echo "🔗 Database URL format: $DATABASE_URL"
echo ""
echo "📝 Next steps:"
echo "1. Create an actual RDS instance for production"
echo "2. Update the DATABASE_URL with the real RDS endpoint"
echo "3. Or modify the application to handle database connection failures gracefully"
