# Security Guidelines

This document outlines the security measures and best practices implemented in the Theobroma Geo API project.

## 🔒 Recent Security Fixes

### GitGuardian Issues Resolved

The following security vulnerabilities detected by GitGuardian have been addressed:

1. **Hardcoded Database Credentials** ✅ **FIXED**
   - Removed hardcoded passwords from `.env` and `.env.staging` files
   - Replaced with environment variable references
   - Added validation to ensure required secrets are provided

2. **AWS RDS Endpoints Exposed** ✅ **FIXED**
   - Removed real AWS RDS endpoints from configuration files
   - Updated scripts to use environment variables
   - Created secure configuration templates

3. **Sensitive Information in Scripts** ✅ **FIXED**
   - Updated `create-staging-db.sh` and `setup_rds.sh` scripts
   - Added environment variable validation
   - Removed hardcoded credentials

## 🛡️ Security Implementation

### Environment Variables

All sensitive configuration is now handled through environment variables:

```bash
# Required environment variables
export DATABASE_URL="postgresql://user:password@host:port/database"
export DB_PASSWORD="your-secure-password"
export AWS_REGION="us-east-2"
```

### Configuration Files

- `.env.template` - Template for local development
- `.env.example` - Documentation and examples
- `.env*` files are excluded from version control via `.gitignore`

### Database Scripts

AWS RDS setup scripts now require environment variables:

```bash
# Secure usage
DB_PASSWORD='secure-password-here' ./create-staging-db.sh
```

## 🔐 Best Practices

### 1. Secrets Management

- **Never** commit credentials to version control
- Use environment variables for all sensitive data
- Consider using dedicated secrets management services:
  - AWS Secrets Manager
  - Azure Key Vault
  - HashiCorp Vault
  - Kubernetes Secrets

### 2. Database Security

- Use strong, unique passwords for each environment
- Implement least-privilege database users
- Rotate credentials regularly
- Use SSL/TLS for database connections
- Restrict database access by IP/security groups

### 3. Environment Separation

- Separate credentials for each environment (dev/staging/prod)
- Use different database instances for each environment
- Implement proper access controls and audit logging

### 4. CI/CD Security

GitHub Actions workflows use secure practices:

```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  DB_PASSWORD: ${{ secrets.STAGING_DB_PASSWORD }}
```

Store secrets in:
- GitHub Secrets for GitHub Actions
- CI/CD platform secret management
- Cloud provider secrets management

## 🚨 Security Checklist

### Before Deployment

- [ ] All environment variables are set via secure methods
- [ ] No hardcoded credentials in any files
- [ ] Database users follow least-privilege principle
- [ ] SSL/TLS enabled for all connections
- [ ] Security groups properly configured
- [ ] Audit logging enabled

### Regular Security Tasks

- [ ] Rotate database passwords monthly
- [ ] Review security group rules quarterly
- [ ] Update dependencies regularly
- [ ] Monitor for security vulnerabilities
- [ ] Review access logs

## 🔍 Security Monitoring

### GitGuardian Integration

- Continuously monitors repository for secrets
- Alerts on potential security issues
- Integrates with development workflow

### Logging and Monitoring

- Database connection monitoring
- Failed authentication attempts
- Unusual query patterns
- Performance anomalies

## 📞 Security Incident Response

### If Credentials Are Compromised

1. **Immediate Actions**:
   - Rotate affected credentials immediately
   - Review access logs for unauthorized usage
   - Update all systems with new credentials

2. **Investigation**:
   - Identify scope of potential exposure
   - Check for unauthorized data access
   - Document incident timeline

3. **Prevention**:
   - Review security practices
   - Update procedures to prevent recurrence
   - Consider additional monitoring

## 🛠️ Tools and Resources

### Security Scanning

- **GitGuardian**: Secret detection in repositories
- **Safety**: Python dependency vulnerability scanning
- **Bandit**: Python code security analysis

### Installation

```bash
# Install security tools
pip install safety bandit

# Run security scans
safety check
bandit -r . -f json
```

### Monitoring Services

- AWS CloudTrail (for AWS resources)
- Database audit logs
- Application performance monitoring (APM)

## 📋 Compliance

### Data Protection

- Implement appropriate data retention policies
- Ensure GDPR/privacy regulation compliance
- Use encryption at rest and in transit
- Regular security assessments

### Access Control

- Multi-factor authentication (MFA) for admin access
- Role-based access control (RBAC)
- Regular access reviews
- Principle of least privilege

---

## 📚 Additional Resources

- [OWASP Security Guidelines](https://owasp.org/)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-learning/)
- [PostgreSQL Security Documentation](https://www.postgresql.org/docs/current/security.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Last Updated**: 2024-07-24
**Security Contact**: security@theobroma.digital
