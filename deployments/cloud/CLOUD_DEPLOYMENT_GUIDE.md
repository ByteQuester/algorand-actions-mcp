# ☁️ Cloud Deployment Guide - Algorand Lending Platform

Complete guide for deploying the Algorand Lending Platform across major cloud providers.

## 📋 Table of Contents

1. [Overview](#overview)
2. [AWS Deployment](#aws-deployment)
3. [Google Cloud Platform](#gcp-deployment)
4. [Azure Deployment](#azure-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Multi-Cloud Strategy](#multi-cloud-strategy)
7. [Cost Optimization](#cost-optimization)
8. [Monitoring & Observability](#monitoring--observability)

---

## 🌐 Overview

### Supported Deployment Models

| Platform | Container Service | Database | Load Balancer | Monitoring |
|----------|------------------|----------|---------------|------------|
| **AWS** | ECS Fargate | RDS PostgreSQL | ALB | CloudWatch |
| **GCP** | Cloud Run | Cloud SQL | Cloud LB | Cloud Monitoring |
| **Azure** | Container Instances | Azure Database | App Gateway | Azure Monitor |
| **Kubernetes** | Any K8s Cluster | PostgreSQL | Ingress | Prometheus/Grafana |

### Architecture Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│    Frontend     │────│      API        │
│   (ALB/CLB/AG)  │    │  (Lending UI)   │    │  (Lending API)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │   Blockchain    │─────────────┘
                       │  MCP Services   │
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │    Database     │
                       │  (PostgreSQL)   │
                       └─────────────────┘
```

---

## 🚀 AWS Deployment

### Prerequisites

- AWS CLI configured
- Docker installed and configured
- VPC with public/private subnets
- ECR repositories created

### Quick Start

```bash
# 1. Set up environment
export AWS_REGION=us-east-1
export AWS_VPC_ID=vpc-12345678
export AWS_SUBNET_1=subnet-12345678
export AWS_SUBNET_2=subnet-87654321
export AWS_SECURITY_GROUP=sg-12345678

# 2. Build and push images to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build images
docker build -t algorand-lending-api .
docker tag algorand-lending-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/algorand-lending-api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/algorand-lending-api:latest

# 3. Deploy with ECS
docker compose -f deployments/cloud/aws/docker-compose.aws.yml up -d
```

### AWS Infrastructure Setup

#### 1. Create RDS PostgreSQL Instance

```bash
aws rds create-db-instance \
    --db-instance-identifier algorand-lending-db \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 15.3 \
    --master-username lending_admin \
    --master-user-password "$(openssl rand -base64 32)" \
    --allocated-storage 100 \
    --vpc-security-group-ids $AWS_SECURITY_GROUP \
    --db-subnet-group-name algorand-lending-subnet-group \
    --backup-retention-period 7 \
    --multi-az \
    --storage-encrypted
```

#### 2. Create ElastiCache Redis Cluster

```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id algorand-lending-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1 \
    --security-group-ids $AWS_SECURITY_GROUP \
    --subnet-group-name algorand-lending-cache-subnet-group
```

#### 3. Create ECS Cluster

```bash
aws ecs create-cluster \
    --cluster-name algorand-lending \
    --capacity-providers FARGATE \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1
```

#### 4. Create Application Load Balancer

```bash
aws elbv2 create-load-balancer \
    --name algorand-lending-alb \
    --subnets $AWS_SUBNET_1 $AWS_SUBNET_2 \
    --security-groups $AWS_SECURITY_GROUP \
    --scheme internet-facing \
    --type application
```

### AWS Secrets Manager Integration

```bash
# Store database password
aws secretsmanager create-secret \
    --name "algorand-lending/database/password" \
    --description "PostgreSQL database password for Algorand Lending Platform" \
    --secret-string "$(openssl rand -base64 32)"

# Store JWT secret
aws secretsmanager create-secret \
    --name "algorand-lending/jwt/secret" \
    --description "JWT secret key for authentication" \
    --secret-string "$(openssl rand -base64 64)"
```

### Cost Optimization

- **Use Spot Instances**: For non-critical workloads
- **Reserved Instances**: For predictable workloads
- **Auto Scaling**: Configure based on CPU/memory metrics
- **S3 Lifecycle Policies**: For backup storage

---

## 🔵 GCP Deployment

### Prerequisites

- gcloud CLI configured
- Docker configured for Google Container Registry
- Project with necessary APIs enabled

### Quick Start

```bash
# 1. Set up environment
export PROJECT_ID=your-gcp-project
export REGION=us-central1
export CLUSTER_NAME=algorand-lending

# 2. Configure Docker for GCR
gcloud auth configure-docker

# 3. Build and push images
docker build -t gcr.io/$PROJECT_ID/algorand-lending-api:latest .
docker push gcr.io/$PROJECT_ID/algorand-lending-api:latest

# 4. Deploy to Cloud Run
gcloud run deploy algorand-lending-api \
    --image gcr.io/$PROJECT_ID/algorand-lending-api:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated
```

### GCP Infrastructure Setup

#### 1. Create Cloud SQL PostgreSQL Instance

```bash
gcloud sql instances create algorand-lending-db \
    --database-version=POSTGRES_15 \
    --tier=db-custom-2-4096 \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=100GB \
    --backup \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04
```

#### 2. Create GKE Cluster (Alternative)

```bash
gcloud container clusters create algorand-lending \
    --num-nodes=3 \
    --machine-type=e2-standard-4 \
    --region=$REGION \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=10 \
    --enable-autorepair \
    --enable-autoupgrade
```

#### 3. Setup Cloud Load Balancer

```bash
gcloud compute forwarding-rules create algorand-lending-lb \
    --global \
    --target-http-proxy=algorand-lending-proxy \
    --ports=80,443
```

### Cost Optimization

- **Preemptible VMs**: For batch workloads
- **Sustained Use Discounts**: Automatic for long-running instances
- **Custom Machine Types**: Right-size your resources
- **Cloud Storage Lifecycle**: Manage backup costs

---

## 🔷 Azure Deployment

### Prerequisites

- Azure CLI configured
- Docker configured for Azure Container Registry
- Resource group created

### Quick Start

```bash
# 1. Set up environment
export RESOURCE_GROUP=algorand-lending-rg
export LOCATION=eastus
export ACR_NAME=algorandlendingacr

# 2. Create Azure Container Registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# 3. Build and push images
az acr build --registry $ACR_NAME --image algorand-lending-api:latest .

# 4. Deploy to Container Instances
az container create \
    --resource-group $RESOURCE_GROUP \
    --name algorand-lending-api \
    --image $ACR_NAME.azurecr.io/algorand-lending-api:latest \
    --cpu 2 \
    --memory 4 \
    --ports 8003 \
    --dns-name-label algorand-lending-api
```

### Azure Infrastructure Setup

#### 1. Create Azure Database for PostgreSQL

```bash
az postgres server create \
    --resource-group $RESOURCE_GROUP \
    --name algorand-lending-db \
    --location $LOCATION \
    --admin-user lending_admin \
    --admin-password "$(openssl rand -base64 32)" \
    --sku-name GP_Gen5_2 \
    --storage-size 102400 \
    --backup-retention 7 \
    --geo-redundant-backup Enabled
```

#### 2. Create Azure Cache for Redis

```bash
az redis create \
    --resource-group $RESOURCE_GROUP \
    --name algorand-lending-redis \
    --location $LOCATION \
    --sku Basic \
    --vm-size c0
```

#### 3. Create Application Gateway

```bash
az network application-gateway create \
    --resource-group $RESOURCE_GROUP \
    --name algorand-lending-ag \
    --location $LOCATION \
    --capacity 2 \
    --sku Standard_v2 \
    --public-ip-address algorand-lending-pip \
    --vnet-name algorand-lending-vnet \
    --subnet algorand-lending-subnet
```

### Cost Optimization

- **Azure Reserved Instances**: For predictable workloads
- **Azure Hybrid Benefit**: Use existing licenses
- **Auto-scaling**: Configure for container instances
- **Cool/Archive Storage**: For backups

---

## ⚓ Kubernetes Deployment

### Prerequisites

- kubectl configured and connected to cluster
- Docker registry access configured
- Helm (optional, for package management)

### Quick Start

```bash
# 1. Clone and setup
git clone <repository>
cd deployments/cloud/kubernetes

# 2. Configure environment
export REGISTRY=your-registry.com
export DOMAIN=lending.yourdomain.com
export IMAGE_TAG=latest

# 3. Deploy
./deploy.sh --registry $REGISTRY --domain $DOMAIN --tag $IMAGE_TAG
```

### Manual Deployment Steps

#### 1. Create Namespace and RBAC

```bash
kubectl apply -f namespace.yml
```

#### 2. Deploy Secrets and ConfigMaps

```bash
# Update secrets with your values
kubectl apply -f configmaps-secrets.yml
```

#### 3. Deploy Database

```bash
kubectl apply -f postgresql-deployment.yml
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
```

#### 4. Deploy Application Services

```bash
kubectl apply -f lending-api-deployment.yml
kubectl apply -f mcp-services-deployment.yml
kubectl apply -f lending-ui-deployment.yml
```

#### 5. Deploy Monitoring

```bash
kubectl apply -f monitoring/
```

#### 6. Configure Ingress

```bash
kubectl apply -f ingress.yml
```

### Cluster Requirements

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| **API** | 1-2 cores | 1-2GB | - |
| **UI** | 0.5-1 core | 512MB-1GB | - |
| **MCP Services** | 0.5-1 core | 512MB | - |
| **PostgreSQL** | 1-2 cores | 2-4GB | 50-100GB |
| **Redis** | 0.5-1 core | 512MB | 10GB |
| **Monitoring** | 1-2 cores | 2-4GB | 50GB |

### Scaling Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: lending-api-hpa
  namespace: algorand-lending
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: lending-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 🌐 Multi-Cloud Strategy

### Benefits

- **High Availability**: Reduce single-cloud dependency
- **Cost Optimization**: Choose best pricing for each service
- **Compliance**: Meet regional data requirements
- **Performance**: Deploy closer to users

### Implementation Approaches

#### 1. Active-Passive Setup

- **Primary**: Full deployment on preferred cloud
- **Secondary**: Standby deployment for disaster recovery
- **Data Sync**: Regular backups and replication

#### 2. Active-Active Setup

- **Load Distribution**: Traffic split across clouds
- **Data Consistency**: Shared database or sync mechanisms
- **Complexity**: Higher operational overhead

#### 3. Service Distribution

- **Frontend**: CDN across multiple regions
- **API**: Primary cloud with failover
- **Database**: Single cloud with cross-region replication
- **Monitoring**: Centralized across all deployments

### Traffic Routing

```yaml
# Example DNS configuration for multi-cloud
api.lending.com:
  - AWS ELB: weight 70
  - GCP Load Balancer: weight 20
  - Azure App Gateway: weight 10
  - Health checks: enabled
  - Failover: automatic
```

---

## 💰 Cost Optimization

### General Strategies

1. **Right-sizing Resources**
   - Monitor actual usage vs. allocated resources
   - Use auto-scaling to match demand
   - Regular resource audits

2. **Reserved Capacity**
   - AWS Reserved Instances
   - GCP Committed Use Discounts
   - Azure Reserved VM Instances

3. **Spot/Preemptible Instances**
   - Use for batch processing
   - Non-critical workloads
   - Development environments

4. **Storage Optimization**
   - Lifecycle policies for backups
   - Appropriate storage classes
   - Data compression and deduplication

### Cost Monitoring Tools

| Cloud | Native Tool | Third-Party |
|-------|-------------|-------------|
| **AWS** | Cost Explorer, Budgets | CloudCheckr, CloudHealth |
| **GCP** | Cloud Billing, Budgets | RightScale, Turbonomic |
| **Azure** | Cost Management | CloudMonix, Densify |

### Sample Monthly Costs

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| **API (2x medium)** | $150 | $140 | $160 |
| **UI (2x small)** | $75 | $70 | $80 |
| **Database** | $200 | $180 | $220 |
| **Load Balancer** | $25 | $20 | $30 |
| **Monitoring** | $50 | $45 | $55 |
| **Total** | **$500** | **$455** | **$545** |

---

## 📊 Monitoring & Observability

### Metrics to Track

#### Application Metrics
- Request rate and latency
- Error rates (4xx, 5xx)
- Transaction throughput
- User registration/login rates

#### Infrastructure Metrics
- CPU and memory utilization
- Network I/O
- Disk usage and I/O
- Container restart counts

#### Business Metrics
- Active loans
- Transaction volumes
- User growth
- Revenue metrics

### Alerting Rules

```yaml
# Example Prometheus alerting rules
groups:
- name: lending-platform
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"

  - alert: APILatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "API latency is high"

  - alert: DatabaseConnections
    expr: postgresql_stat_database_numbackends > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High database connection count"
```

### Log Aggregation

#### Centralized Logging Stack

1. **Log Collection**: Fluent Bit, Filebeat
2. **Log Processing**: Logstash, Fluentd
3. **Log Storage**: Elasticsearch, CloudWatch Logs
4. **Log Visualization**: Kibana, Grafana

#### Log Format Standardization

```json
{
  "timestamp": "2025-09-14T12:00:00Z",
  "level": "INFO",
  "service": "lending-api",
  "trace_id": "abc123",
  "user_id": "user456",
  "message": "Loan application submitted",
  "metadata": {
    "loan_id": "loan789",
    "amount": 10000,
    "duration": 12
  }
}
```

### Distributed Tracing

- **Jaeger** or **Zipkin** for trace collection
- **OpenTelemetry** for instrumentation
- **Service mesh** (Istio, Linkerd) for automatic tracing

---

## 🚨 Disaster Recovery

### Backup Strategy

#### Data Backups
- **PostgreSQL**: Daily automated backups with 30-day retention
- **Application Data**: S3/GCS with versioning and lifecycle policies
- **Configuration**: Git-based infrastructure as code

#### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Restore from backup
   pg_restore --host=new-host --username=user --dbname=lending_db backup.sql
   ```

2. **Application Recovery**
   ```bash
   # Deploy to new environment
   ./deploy.sh --emergency --backup-date=2025-09-14
   ```

3. **DNS Failover**
   ```bash
   # Update DNS to point to backup environment
   aws route53 change-resource-record-sets --hosted-zone-id Z123 --change-batch file://failover.json
   ```

### Testing Procedures

- **Monthly**: Backup restoration tests
- **Quarterly**: Full disaster recovery drills
- **Annually**: Multi-cloud failover tests

---

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Infrastructure provisioned and configured
- [ ] Docker images built and pushed to registry
- [ ] Secrets and configuration updated
- [ ] Database migrations prepared
- [ ] Monitoring and alerting configured

### Deployment

- [ ] Deploy database and wait for readiness
- [ ] Deploy backend services (API, MCP)
- [ ] Deploy frontend services (UI)
- [ ] Configure load balancer and ingress
- [ ] Verify health checks pass

### Post-Deployment

- [ ] Run smoke tests
- [ ] Verify monitoring dashboards
- [ ] Test backup procedures
- [ ] Update documentation
- [ ] Notify stakeholders

### Rollback Plan

- [ ] Database backup created before deployment
- [ ] Previous container images available
- [ ] Rollback procedure documented and tested
- [ ] Automated rollback triggers configured

---

## 📞 Support and Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs
kubectl logs deployment/lending-api -n algorand-lending
docker logs container-name

# Check resources
kubectl describe pod pod-name -n algorand-lending
```

#### 2. Database Connection Failed
```bash
# Test connectivity
pg_isready -h database-host -p 5432 -U username

# Check security groups/firewall rules
# Verify connection string and credentials
```

#### 3. High Memory Usage
```bash
# Check memory usage
kubectl top pods -n algorand-lending
docker stats

# Adjust resource limits
kubectl patch deployment lending-api -p '{"spec":{"template":{"spec":{"containers":[{"name":"lending-api","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
```

### Getting Help

- **Documentation**: Check cloud provider documentation
- **Community**: GitHub Issues, Stack Overflow
- **Support**: Cloud provider support channels
- **Monitoring**: Use observability tools to identify issues

---

**🎉 Your Algorand Lending Platform is now ready for production deployment across any cloud provider!**