import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.lstm_dataset import prepare_lstm_data

class LSTMForecast(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2, output_size=1, dropout=0.2):
        super(LSTMForecast, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layer
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Output layer
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        # Initialize hidden and cell states
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Decode the hidden state of the last time step
        out = self.fc(out[:, -1, :])
        return out

def train_lstm(ticker="^GSPC", epochs=50, batch_size=32, learning_rate=0.001):
    print(f"\n--- Training LSTM for {ticker} ---")
    
    # 1. Prepare Data
    seq_length = 21
    data = prepare_lstm_data(ticker, sequence_length=seq_length)
    if data is None:
        return
        
    X_train, y_train, X_test, y_test = data
    
    # Check if GPU is available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}")
    
    X_train, y_train = X_train.to(device), y_train.to(device)
    X_test, y_test = X_test.to(device), y_test.to(device)
    
    # Create DataLoaders
    train_dataset = TensorDataset(X_train, y_train)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    # 2. Initialize Model
    input_size = X_train.shape[2] # Number of features
    model = LSTMForecast(input_size=input_size).to(device)
    
    # Loss and Optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # 3. Train the Model
    print("Starting training...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            
            # Backward pass and optimize
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        # Print progress
        if (epoch+1) % 10 == 0:
            model.eval()
            with torch.no_grad():
                test_outputs = model(X_test)
                test_loss = criterion(test_outputs, y_test)
            print(f"Epoch [{epoch+1}/{epochs}], Train Loss: {total_loss/len(train_loader):.6f}, Test Loss: {test_loss.item():.6f}")
            
    # 4. Save the Model
    models_dir = f"models/{ticker.replace('-', '_')}"
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, "lstm_model.pth")
    torch.save(model.state_dict(), model_path)
    print(f"Model successfully saved to {model_path}")

if __name__ == "__main__":
    # Train on a few sample tickers if run directly
    for t in ["^GSPC", "BTC-USD", "TSLA"]:
        train_lstm(t)
