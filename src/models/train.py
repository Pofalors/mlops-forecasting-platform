import argparse
import mlflow
import sys
import os

# Προσθέτω το path για imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.data_loader import DataLoader
from models.model import EnergyForecastingModel

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-path', required=True)
    parser.add_argument('--input-steps', type=int, default=48)
    parser.add_argument('--output-steps', type=int, default=24)
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--batch-size', type=int, default=32)
    args = parser.parse_args()
    
    print(f"Starting training with data: {args.data-path}")
    
    # Set MLflow tracking
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("energy_forecasting")
    
    # Load data
    loader = DataLoader(args.data_path)
    df = loader.load_data()
    print(f"Data loaded: {len(df)} rows")
    
    # Prepare sequences
    X_train, X_val, X_test, y_train, y_val, y_test = loader.prepare_sequences(
        df, args.input_steps, args.output_steps
    )
    print(f"Training data shape: {X_train.shape}")
    
    # Train model
    model = EnergyForecastingModel(args.input_steps, args.output_steps)
    model.build_model()
    print("Model built")
    
    with mlflow.start_run():
        mlflow.log_params({
            "input_steps": args.input_steps,
            "output_steps": args.output_steps,
            "epochs": args.epochs,
            "batch_size": args.batch_size
        })
        
        results = model.train(X_train, y_train, X_val, y_val, 
                             args.epochs, args.batch_size)
        
        mlflow.log_metric("final_loss", results['final_loss'])
        print(f"Training completed! Loss: {results['final_loss']}")

if __name__ == '__main__':
    main()
