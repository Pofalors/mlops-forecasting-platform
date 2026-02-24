param(
    [string]$Command = "help"
)

$composeFile = "docker-compose.yml"

switch ($Command) {
    "build" {
        docker-compose -f $composeFile build
    }
    "up" {
        docker-compose -f $composeFile up -d
        Write-Host "Services started:" -ForegroundColor Green
        Write-Host "  - MLflow: http://localhost:5001" -ForegroundColor Yellow
        Write-Host "  - API: http://localhost:5000" -ForegroundColor Yellow
    }
    "down" {
        docker-compose -f $composeFile down
    }
    "train" {
        docker-compose -f $composeFile --profile training run --rm training `
            --data-path /app/data/energy_data.csv `
            --input-steps 48 `
            --output-steps 24 `
            --epochs 5
    }
    "logs" {
        docker-compose -f $composeFile logs -f
    }
    "clean" {
        docker-compose -f $composeFile down -v
        docker system prune -f
    }
    "ps" {
        docker-compose -f $composeFile ps
    }
    "restart" {
        docker-compose -f $composeFile restart
    }
    default {
        Write-Host "Commands:" -ForegroundColor Cyan
        Write-Host "  .\run.ps1 build    - Build images"
        Write-Host "  .\run.ps1 up       - Start services"
        Write-Host "  .\run.ps1 down     - Stop services"
        Write-Host "  .\run.ps1 train    - Run training"
        Write-Host "  .\run.ps1 logs     - View logs"
        Write-Host "  .\run.ps1 clean    - Clean everything"
        Write-Host "  .\run.ps1 ps       - List services"
    }
}