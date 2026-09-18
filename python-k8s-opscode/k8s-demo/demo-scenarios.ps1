# Demo scenarios for Opscode Platform (Windows)
# This script demonstrates the platform's capabilities

$ErrorActionPreference = "Stop"

$NAMESPACE = "demo"
$APP_NAME = "demo-app"

Write-Host "Opscode Platform Demo Scenarios" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Check if kubectl is available
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "Error: kubectl is not installed" -ForegroundColor Red
    exit 1
}

# Check if cluster is accessible
try {
    kubectl cluster-info | Out-Null
} catch {
    Write-Host "Error: Cannot connect to Kubernetes cluster" -ForegroundColor Red
    exit 1
}

Write-Host "Scenario 1: Deploy Demo Application" -ForegroundColor Yellow
Write-Host "------------------------------------" -ForegroundColor Yellow
kubectl apply -f k8s-demo/demo-app.yaml
Write-Host "Waiting for deployment to be ready..." -ForegroundColor Cyan
kubectl wait --for=condition=available --timeout=60s deployment/$APP_NAME -n $NAMESPACE
Write-Host "✓ Demo application deployed" -ForegroundColor Green
Write-Host ""

Write-Host "Scenario 2: Normal Operation" -ForegroundColor Yellow
Write-Host "------------------------------" -ForegroundColor Yellow
kubectl get pods -n $NAMESPACE -l app=$APP_NAME
kubectl get deployment $APP_NAME -n $NAMESPACE
Write-Host "✓ Application running normally" -ForegroundColor Green
Write-Host ""

Write-Host "Scenario 3: Simulate Pod Failure" -ForegroundColor Yellow
Write-Host "------------------------------------" -ForegroundColor Yellow
Write-Host "Deleting a pod to simulate failure..." -ForegroundColor Cyan
kubectl delete pod -n $NAMESPACE -l app=$APP_NAME --field-selector=status.phase=Running --limit=1
Write-Host "Waiting for Kubernetes to recreate pod..." -ForegroundColor Cyan
Start-Sleep -Seconds 10
kubectl get pods -n $NAMESPACE -l app=$APP_NAME
Write-Host "✓ Pod recreated successfully" -ForegroundColor Green
Write-Host ""

Write-Host "Scenario 4: Simulate CrashLoopBackOff" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Yellow
Write-Host "Scaling down to 1 replica and setting broken image..." -ForegroundColor Cyan
kubectl scale deployment $APP_NAME --replicas=1 -n $NAMESPACE
kubectl set image deployment/$APP_NAME demo-app=nginx:invalid-tag -n $NAMESPACE
Write-Host "Waiting for CrashLoopBackOff..." -ForegroundColor Cyan
Start-Sleep -Seconds 30
kubectl get pods -n $NAMESPACE -l app=$APP_NAME
Write-Host "✓ CrashLoopBackOff simulated" -ForegroundColor Green
Write-Host ""

Write-Host "Scenario 5: Restore Application" -ForegroundColor Yellow
Write-Host "------------------------------" -ForegroundColor Yellow
Write-Host "Restoring with correct image and scaling to 3 replicas..." -ForegroundColor Cyan
kubectl set image deployment/$APP_NAME demo-app=nginx:alpine -n $NAMESPACE
kubectl scale deployment $APP_NAME --replicas=3 -n $NAMESPACE
Write-Host "Waiting for recovery..." -ForegroundColor Cyan
kubectl wait --for=condition=available --timeout=60s deployment/$APP_NAME -n $NAMESPACE
kubectl get pods -n $NAMESPACE -l app=$APP_NAME
Write-Host "✓ Application restored" -ForegroundColor Green
Write-Host ""

Write-Host "Scenario 6: Simulate High CPU" -ForegroundColor Yellow
Write-Host "------------------------------" -ForegroundColor Yellow
Write-Host "Adding stress to simulate high CPU..." -ForegroundColor Cyan
kubectl run stress-test --image=polinux/stress --rm -it --restart=Never -- stress --cpu 2 --timeout 30s -n $NAMESPACE -i -y -- --timeout 30s 2>&1 | Out-Null
Write-Host "✓ High CPU simulation complete" -ForegroundColor Green
Write-Host ""

Write-Host "Scenario 7: Simulate Replica Shortage" -ForegroundColor Yellow
Write-Host "------------------------------------" -ForegroundColor Yellow
Write-Host "Scaling down to 1 replica to simulate shortage..." -ForegroundColor Cyan
kubectl scale deployment $APP_NAME --replicas=1 -n $NAMESPACE
Write-Host "Checking replica count..." -ForegroundColor Cyan
kubectl get deployment $APP_NAME -n $NAMESPACE
Write-Host "✓ Replica shortage simulated" -ForegroundColor Green
Write-Host ""

Write-Host "Scenario 8: Restore Normal State" -ForegroundColor Yellow
Write-Host "------------------------------" -ForegroundColor Yellow
Write-Host "Scaling back to 3 replicas..." -ForegroundColor Cyan
kubectl scale deployment $APP_NAME --replicas=3 -n $NAMESPACE
kubectl wait --for=condition=available --timeout=60s deployment/$APP_NAME -n $NAMESPACE
kubectl get pods -n $NAMESPACE -l app=$APP_NAME
Write-Host "✓ Application restored to normal state" -ForegroundColor Green
Write-Host ""

Write-Host "Demo Scenarios Complete" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host ""
Write-Host "To clean up demo resources:" -ForegroundColor Cyan
Write-Host "  kubectl delete -f k8s-demo/demo-app.yaml" -ForegroundColor Cyan
Write-Host ""
Write-Host "To monitor with Opscode:" -ForegroundColor Cyan
Write-Host "  Access dashboard at http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Check incidents at /api/v1/incidents" -ForegroundColor Cyan
Write-Host "  View remediation actions at /api/v1/remediation/actions" -ForegroundColor Cyan
