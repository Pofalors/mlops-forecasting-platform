#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
MODULE: Energy Forecasting API
PURPOSE: Production-ready REST API for energy consumption predictions
         using trained ML models from MLflow registry.
AUTHOR: FANIS SPANOS
DATE: 2026-02-23
VERSION: 1.0.0

DESCRIPTION:
    This Flask application serves machine learning models for energy forecasting.
    It automatically loads the latest production model from MLflow registry
    and provides endpoints for health checks and predictions.

ENDPOINTS:
    GET  /health          - Health check endpoint
    POST /predict         - Make predictions with loaded model

DEPENDENCIES:
    - flask==2.3.3        : Web framework
    - mlflow==2.8.0       : Model registry client
    - numpy==1.24.3       : Numerical operations
    - pandas==2.0.3       : Data manipulation (if needed)
    - prometheus-flask-exporter==0.23.0 : Metrics for monitoring

ENVIRONMENT VARIABLES:
    - MLFLOW_TRACKING_URI : MLflow server URI (default: http://mlflow:5000)
    - MODEL_URI          : Specific model URI to load (optional)
    - FLASK_ENV          : Development/production mode
    - LOG_LEVEL          : Logging level (INFO, DEBUG, etc.)

USAGE EXAMPLES:
    1. Health check:
        curl http://localhost:5000/health
    
    2. Make prediction:
        curl -X POST http://localhost:5000/predict \
          -H "Content-Type: application/json" \
          -d '{"sequences": [[0.1, 0.2, 0.3, ...]]}'

================================================================================
"""

# ==============================================================================
# IMPORTS
# ==============================================================================

import os
import logging
import sys
from typing import Dict, Any, Optional, List, Union

import numpy as np
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Configure logging with detailed format
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
        #logging.FileHandler('/app/logs/api.log')  # Optional: log to file
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize Prometheus metrics for monitoring
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Energy Forecasting API', version='1.0.0')

# ==============================================================================
# MODEL LOADING
# ==============================================================================

class ModelLoader:
    """
    Handles loading and management of ML models from MLflow registry.
    
    This class implements a fallback strategy:
    1. Try to load production model from MLflow registry
    2. If not found, load the latest trained model
    3. If all fails, use dummy predictions
    
    Attributes:
        model: Loaded MLflow model
        model_version: Version/ID of loaded model
        mlflow_tracking_uri: URI of MLflow tracking server
    """
    
    def __init__(self, tracking_uri: str = "http://mlflow:5000"):
        """
        Initialize ModelLoader with MLflow tracking URI.
        
        Args:
            tracking_uri: MLflow server URI (default: http://mlflow:5000)
        """
        self.model: Optional[mlflow.pyfunc.PyFuncModel] = None
        self.model_version: str = "none"
        self.mlflow_tracking_uri = tracking_uri
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient(tracking_uri=tracking_uri)
        
        logger.info(f"ModelLoader initialized with tracking URI: {tracking_uri}")
    
    def load_production_model(self) -> bool:
        """
        Attempt to load the production model from MLflow registry.
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            # Try to load production model from registry
            model_uri = "models:/energy_forecasting_model/Production"
            logger.info(f"Attempting to load production model from: {model_uri}")
            
            self.model = mlflow.pyfunc.load_model(model_uri)
            self.model_version = "production"
            
            logger.info("✅ Successfully loaded production model")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load production model: {str(e)}")
            return False
    
    def load_latest_model(self) -> bool:
        """
        Attempt to load the latest trained model from MLflow experiments.
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            # Search for the latest run in experiment 1
            runs = self.client.search_runs(
                experiment_ids=["1"],
                order_by=["start_time DESC"],
                max_results=1
            )
            
            if runs:
                run_id = runs[0].info.run_id
                model_uri = f"runs:/{run_id}/model"
                logger.info(f"Attempting to load latest model from run: {run_id}")
                
                self.model = mlflow.pyfunc.load_model(model_uri)
                self.model_version = run_id[:8]  # First 8 chars of run_id
                
                logger.info(f"✅ Successfully loaded model from run {run_id}")
                return True
            else:
                logger.warning("⚠️ No runs found in experiment 1")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load latest model: {str(e)}")
            return False
    
    def load_model(self) -> None:
        """
        Main method to load model with fallback strategy.
        
        Strategy:
        1. Try production model first
        2. If fails, try latest model
        3. If all fails, use dummy mode
        """
        logger.info("=" * 50)
        logger.info("MODEL LOADING INITIATED")
        logger.info("=" * 50)
        
        # Try production model first
        if self.load_production_model():
            return
        
        # Fallback to latest model
        logger.info("Falling back to latest model...")
        if self.load_latest_model():
            return
        
        # Final fallback: dummy mode
        logger.warning("⚠️ No model found! Using DUMMY predictions")
        self.model_version = "dummy"
        logger.info("=" * 50)


# Initialize model loader
model_loader = ModelLoader()

# Load model on startup
model_loader.load_model()

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.route('/health', methods=['GET'])
@metrics.do_not_track()  # Don't track health checks in metrics
def health_check() -> tuple:
    """
    Health check endpoint for Kubernetes liveness/readiness probes.
    
    Returns:
        tuple: (JSON response, HTTP status code)
        
    Response format:
        {
            "status": "healthy",
            "model": "loaded|dummy",
            "model_version": "production|run_id|dummy",
            "timestamp": "ISO-8601 timestamp"
        }
    
    Example:
        $ curl http://localhost:5000/health
        {
            "status": "healthy",
            "model": "loaded",
            "model_version": "production",
            "timestamp": "2024-02-23T12:00:00Z"
        }
    """
    from datetime import datetime
    
    response = {
        "status": "healthy",
        "model": "loaded" if model_loader.model else "dummy",
        "model_version": model_loader.model_version,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    logger.debug(f"Health check response: {response}")
    return jsonify(response), 200


@app.route('/predict', methods=['POST'])
@metrics.summary('predict_requests', 'Prediction request metrics')
def predict() -> tuple:
    """
    Make predictions using the loaded model.
    
    Expected JSON request format:
        {
            "sequences": [
                [0.1, 0.2, 0.3, ..., 0.4],  # Sequence 1 (length 48)
                [0.2, 0.3, 0.4, ..., 0.5]   # Sequence 2 (optional)
            ]
        }
    
    Returns:
        tuple: (JSON response, HTTP status code)
        
    Response format (success):
        {
            "predictions": [
                [1.2, 1.3, 1.4, ...],  # Predictions for sequence 1 (length 24)
                [1.3, 1.4, 1.5, ...]   # Predictions for sequence 2
            ],
            "model_version": "production|run_id|dummy"
        }
    
    Response format (error):
        {
            "error": "Error description",
            "error_type": "ValueError|KeyError|etc"
        }
    
    Status codes:
        200: Success
        400: Bad request (invalid JSON or missing fields)
        500: Internal server error
    
    Example:
        $ curl -X POST http://localhost:5000/predict \\
            -H "Content-Type: application/json" \\
            -d '{"sequences": [[0.1, 0.2, 0.3, 0.4]]}'
        
        {
            "predictions": [[0.15, 0.25, 0.35, 0.45]],
            "model_version": "production"
        }
    """
    try:
        # Log request details (careful with sensitive data)
        logger.info("Received prediction request")
        
        # ======================================================================
        # INPUT VALIDATION
        # ======================================================================
        
        # Parse JSON data
        data = request.get_json()
        if not data:
            logger.warning("Request received with no JSON data")
            return jsonify({
                "error": "No JSON data provided",
                "error_type": "MissingData"
            }), 400
        
        # Check for sequences field
        if 'sequences' not in data:
            logger.warning("Request missing 'sequences' field")
            return jsonify({
                "error": "Missing 'sequences' field in request",
                "error_type": "MissingField"
            }), 400
        
        # Convert to numpy array
        sequences = np.array(data['sequences'], dtype=np.float32)
        logger.debug(f"Input sequences shape: {sequences.shape}")
        
        # Validate input dimensions
        if sequences.ndim != 2:
            logger.warning(f"Invalid input dimension: {sequences.ndim} (expected 2)")
            return jsonify({
                "error": "Sequences must be a 2D array",
                "error_type": "InvalidDimension"
            }), 400
        
        # ======================================================================
        # PREDICTION
        # ======================================================================
        
        # Make predictions (either with model or dummy)
        if model_loader.model and len(sequences) > 0:
            # Real model predictions
            logger.info(f"Making predictions with model: {model_loader.model_version}")
            predictions = model_loader.model.predict(sequences)
            
            # Convert to list for JSON serialization
            predictions_list = predictions.tolist() if hasattr(predictions, 'tolist') else predictions
            
        else:
            # Dummy predictions for testing
            logger.info("Using dummy predictions (no model loaded)")
            # Generate random predictions matching output shape (assuming 24 steps)
            predictions_list = np.random.randn(sequences.shape[0], 24).tolist()
        
        # ======================================================================
        # RESPONSE
        # ======================================================================
        
        response = {
            "predictions": predictions_list,
            "model_version": model_loader.model_version
        }
        
        logger.info(f"Prediction successful. Output shape: {len(predictions_list)} sequences")
        return jsonify(response), 200
        
    except ValueError as e:
        # Handle JSON parsing errors
        logger.error(f"ValueError during prediction: {str(e)}")
        return jsonify({
            "error": f"Invalid data format: {str(e)}",
            "error_type": "ValueError"
        }), 400
        
    except KeyError as e:
        # Handle missing keys
        logger.error(f"KeyError during prediction: {str(e)}")
        return jsonify({
            "error": f"Missing key in request: {str(e)}",
            "error_type": "KeyError"
        }), 400
        
    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error during prediction: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "error_type": type(e).__name__
        }), 500


@app.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Prometheus metrics endpoint for monitoring.
    
    This endpoint exposes metrics in Prometheus format:
        - Request counts
        - Request latencies
        - Prediction values distribution
        - Model version info
    
    Returns:
        str: Prometheus formatted metrics
    """
    return '', 204  # Prometheus metrics are handled by the exporter


@app.route('/info', methods=['GET'])
def model_info() -> tuple:
    """
    Get information about the currently loaded model.
    
    Returns:
        tuple: (JSON response, HTTP status code)
        
    Response format:
        {
            "model_version": "production|run_id|dummy",
            "model_loaded": true|false,
            "mlflow_tracking_uri": "http://mlflow:5000",
            "endpoints": ["/health", "/predict", "/metrics", "/info"]
        }
    
    Example:
        $ curl http://localhost:5000/info
    """
    response = {
        "model_version": model_loader.model_version,
        "model_loaded": model_loader.model is not None,
        "mlflow_tracking_uri": model_loader.mlflow_tracking_uri,
        "endpoints": ["/health", "/predict", "/metrics", "/info"]
    }
    
    return jsonify(response), 200


# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/health", "/predict", "/metrics", "/info"]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "error_type": "InternalError"
    }), 500


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == '__main__':
    """
    Main entry point for running the Flask application.
    
    When running directly (not through gunicorn), this starts the
    Flask development server. For production, use gunicorn.
    
    Environment variables:
        - FLASK_HOST: Host to bind to (default: 0.0.0.0)
        - FLASK_PORT: Port to bind to (default: 5000)
        - FLASK_DEBUG: Debug mode (default: False)
    """
    logger.info("=" * 50)
    logger.info("ENERGY FORECASTING API STARTING")
    logger.info("=" * 50)
    
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Configuration:")
    logger.info(f"  - Host: {host}")
    logger.info(f"  - Port: {port}")
    logger.info(f"  - Debug: {debug}")
    logger.info(f"  - MLflow URI: {model_loader.mlflow_tracking_uri}")
    logger.info(f"  - Model version: {model_loader.model_version}")
    logger.info("=" * 50)
    
    # Start the Flask application
    app.run(host=host, port=port, debug=debug)