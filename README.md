# MLOps Forecasting Platform

Complete MLOps platform for energy consumption forecasting with Kubernetes.

## 🏗️ Architecture
- **MLflow**: Experiment tracking and model registry
- **Flask API**: Model serving with Prometheus metrics
- **Kubernetes**: Orchestration with auto-scaling
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards

## 📦 Services
| Service | URL | Credentials |
|---------|-----|-------------|
| MLflow | http://localhost:5001 | - |
| API | http://localhost:5000 | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin |

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Minikube
- kubectl
- Python 3.9+

### Local Development with Docker Compose
```bash
# Start all services
docker-compose up -d

# Train model
docker-compose --profile training run --rm training \
  --data-path /app/data/energy_data.csv

# Check logs
docker-compose logs -f api
```

## Kubernetes Deployment (Minikube)
```bash
# Start minikube
minikube start --cpus 4 --memory 4096

# Deploy all components
kubectl apply -k k8s/minikube/

# Check pods
kubectl get pods -n mlops-platform -w

# Port forwarding for local access
kubectl port-forward -n mlops-platform svc/api-service 5000:5000
kubectl port-forward -n mlops-platform svc/mlflow-service 5001:5000
kubectl port-forward -n mlops-platform svc/prometheus-service 9090:9090
kubectl port-forward -n mlops-platform svc/grafana-service 3000:3000
```

## 📊 API Usage

### Health Check
```bash
curl http://localhost:5000/health
```

### Make Prediction (48 input values → 24 predictions)
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sequences": [[0.1, 0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.2, 0.3, 0.4]]
  }'
```

### Get Model Info
```bash
curl http://localhost:5000/info
```

## 📁 Project Structure
```
├── docker/                  # Dockerfiles
│   ├── Dockerfile.api
│   ├── Dockerfile.train
│   └── Dockerfile.mlflow
├── k8s/                      # Kubernetes manifests
│   └── minikube/
│       ├── namespace.yaml
│       ├── configmap.yaml
│       ├── mlflow-deployment.yaml
│       ├── mlflow-service.yaml
│       ├── api-deployment.yaml
│       ├── api-service.yaml
│       ├── prometheus-config.yaml
│       ├── prometheus-deployment.yaml
│       ├── prometheus-service.yaml
│       ├── grafana-datasources.yaml
│       ├── grafana-deployment.yaml
│       ├── grafana-service.yaml
│       └── kustomization.yaml
├── requirements/             # Python dependencies
│   ├── api-requirements.txt
│   ├── train-requirements.txt
│   └── mlflow-requirements.txt
├── src/                      # Source code
│   ├── api/
│   │   └── app.py
│   ├── data/
│   │   └── data_loader.py
│   └── models/
│       ├── model.py
│       └── train.py
├── data/                      # Training data
│   └── energy_data.csv
├── monitoring/                # Monitoring configs
│   └── prometheus/
│       └── prometheus.yml
├── docker-compose.yml
└── README.md
```

## 🛠️ Technologies

- Python 3.9
- TensorFlow 2.15
- Flask
- MLflow
- Kubernetes
- Prometheus
- Grafana
- Docker

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

Fanis Spanos
- GitHub: @Pofalors
- LinkedIn: /in/fanis-spanos-049ab6244/