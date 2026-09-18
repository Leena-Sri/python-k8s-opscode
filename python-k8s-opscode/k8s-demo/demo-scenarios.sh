#!/bin/bash

# Demo scenarios for Opscode Platform
# This script demonstrates the platform's capabilities

set -e

NAMESPACE="demo"
APP_NAME="demo-app"

echo "Opscode Platform Demo Scenarios"
echo "================================"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "Scenario 1: Deploy Demo Application"
echo "------------------------------------"
kubectl apply -f k8s-demo/demo-app.yaml
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=60s deployment/$APP_NAME -n $NAMESPACE
echo "✓ Demo application deployed"
echo ""

echo "Scenario 2: Normal Operation"
echo "------------------------------"
kubectl get pods -n $NAMESPACE -l app=$APP_NAME
kubectl get deployment $APP_NAME -n $NAMESPACE
echo "✓ Application running normally"
echo ""

echo "Scenario 3: Simulate Pod Failure"
echo "--------------------------------"
echo "Deleting a pod to simulate failure..."
kubectl delete pod -n $NAMESPACE -l app=$APP_NAME --field-selector=status.phase=Running --limit=1
echo "Waiting for Kubernetes to recreate pod..."
sleep 10
kubectl get pods -n $NAMESPACE -l app=$APP_NAME
echo "✓ Pod recreated successfully"
echo ""

echo "Scenario 4: Simulate CrashLoopBackOff"
echo "--------------------------------------"
echo "Scaling down to 1 replica and setting broken image..."
kubectl scale deployment $APP_NAME --replicas=1 -n $NAMESPACE
kubectl set image deployment/$APP_NAME demo-app=nginx:invalid-tag -n $NAMESPACE
echo "Waiting for CrashLoopBackOff..."
sleep 30
kubectl get pods -n $NAMESPACE -l app=$APP_NAME
echo "✓ CrashLoopBackOff simulated"
echo ""

echo "Scenario 5: Restore Application"
echo "------------------------------"
echo "Restoring with correct image and scaling to 3 replicas..."
kubectl set image deployment/$APP_NAME demo-app=nginx:alpine -n $NAMESPACE
kubectl scale deployment $APP_NAME --replicas=3 -n $NAMESPACE
echo "Waiting for recovery..."
kubectl wait --for=condition=available --timeout=60s deployment/$APP_NAME -n $NAMESPACE
kubectl get pods -n $NAMESPACE -l app=$APP_NAME
echo "✓ Application restored"
echo ""

echo "Scenario 6: Simulate High CPU"
echo "------------------------------"
echo "Adding stress to simulate high CPU..."
kubectl run stress-test --image=polinux/stress --rm -it --restart=Never -- stress --cpu 2 --timeout 30s -n $NAMESPACE || true
echo "✓ High CPU simulation complete"
echo ""

echo "Scenario 7: Simulate Replica Shortage"
echo "------------------------------------"
echo "Scaling down to 1 replica to simulate shortage..."
kubectl scale deployment $APP_NAME --replicas=1 -n $NAMESPACE
echo "Checking replica count..."
kubectl get deployment $APP_NAME -n $NAMESPACE
echo "✓ Replica shortage simulated"
echo ""

echo "Scenario 8: Restore Normal State"
echo "------------------------------"
echo "Scaling back to 3 replicas..."
kubectl scale deployment $APP_NAME --replicas=3 -n $NAMESPACE
kubectl wait --for=condition=available --timeout=60s deployment/$APP_NAME -n $NAMESPACE
kubectl get pods -n $NAMESPACE -l app=$APP_NAME
echo "✓ Application restored to normal state"
echo ""

echo "Demo Scenarios Complete"
echo "======================="
echo ""
echo "To clean up demo resources:"
echo "  kubectl delete -f k8s-demo/demo-app.yaml"
echo ""
echo "To monitor with Opscode:"
echo "  Access dashboard at http://localhost:8000"
echo "  Check incidents at /api/v1/incidents"
echo "  View remediation actions at /api/v1/remediation/actions"
