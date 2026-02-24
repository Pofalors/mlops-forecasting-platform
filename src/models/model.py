import tensorflow as tf
import numpy as np

class EnergyForecastingModel:
    def __init__(self, input_steps=48, output_steps=24):
        self.input_steps = input_steps
        self.output_steps = output_steps
        self.model = None
        
    def build_model(self):
        self.model = tf.keras.Sequential([
            tf.keras.layers.LSTM(64, input_shape=(self.input_steps, 1)),
            tf.keras.layers.Dense(self.output_steps)
        ])
        self.model.compile(optimizer='adam', loss='mse')
        return self.model
        
    def train(self, X_train, y_train, X_val, y_val, epochs=10, batch_size=32):
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            verbose=1
        )
        return {"final_loss": history.history['loss'][-1]}
        
    def predict(self, X):
        return self.model.predict(X)