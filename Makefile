.PHONY: help build up down train test clean

help:
	@echo "Available commands:"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make train    - Run training job"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up"

build:
	docker-compose -f docker-compose.yml build

up:
	docker-compose -f docker-compose.yml up -d
	@echo "Services started:"
	@echo "  - API: http://localhost:5000"
	@echo "  - MLflow: http://localhost:5001"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"

down:
	docker-compose -f docker-compose.yml down

train:
	docker-compose -f docker-compose.yml --profile training run --rm training \
		--data-path /app/data/energy_data.csv \
		--input-steps ${INPUT_STEPS} \
		--output-steps ${OUTPUT_STEPS} \
		--epochs ${EPOCHS}

test:
	docker-compose -f docker-compose.yml run --rm api pytest tests/ -v

clean:
	docker-compose -f docker-compose.yml down -v
	docker system prune -f

logs:
	docker-compose -f docker-compose.yml logs -f

# Training with custom parameters
train-production:
	$(MAKE) train INPUT_STEPS=48 OUTPUT_STEPS=24 EPOCHS=100

train-quick:
	$(MAKE) train INPUT_STEPS=24 OUTPUT_STEPS=12 EPOCHS=10