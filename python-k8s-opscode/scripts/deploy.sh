#!/bin/bash

# Deploy script for Opscode Platform to Kubernetes
# This script deploys the application to a Kubernetes cluster

set -e

NAMESPACE="opscode"
REGISTRY="your-registry.com"
IMAGE_TAG="latest"

echo "Deploying Opscode Platform to Kubernetes..."

# Build Docker image
echo "Building Docker image..."
docker build -t ${REGISTRY}/python-k8s-opscode:${IMAGE_TAG} .

# Push Docker image
echo "Pushing Docker image..."
docker push ${REGISTRY}/python-k8s-opscode:${IMAGE_TAG}

# Update deployment image
echo "Updating Kubernetes deployment..."
kubectl set image deployment/opscode opscode=${REGISTRY}/python-k8s-opscode:${IMAGE_TAG} -n ${NAMESPACE}

# Wait for rollout to complete
echo "Waiting for rollout to complete..."
kubectl rollout status deployment/opscode -n ${NAMESPACE}

# Get deployment status
echo "Deployment status:"
kubectl get deployment opscode -n ${NAMESPACE}

# Get pods
echo "Pods:"
kubectl get pods -n ${NAMESPACE} -l app=opscode

echo "Deployment complete!"
echo "Service: kubectl get svc opscode -n ${NAMESPACE}"
