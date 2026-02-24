import pandas as pd
import numpy as np

class DataLoader:
    def __init__(self, data_path):
        self.data_path = data_path
        
    def load_data(self):
        return pd.read_csv(self.data_path)
        
    def prepare_sequences(self, data, input_steps, output_steps, train_split=0.8):
        # Απλή υλοποίηση για testing
        X = np.random.randn(100, input_steps, 1)
        y = np.random.randn(100, output_steps)
        
        split = int(len(X) * train_split)
        val_split = int(split * 0.9)
        
        return (X[:val_split], X[val_split:split], X[split:],
                y[:val_split], y[val_split:split], y[split:])