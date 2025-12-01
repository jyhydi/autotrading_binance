import torch
import torch.nn as nn
import torch.nn.functional as F



class IndicatorParamNN(nn.Module):
    """신경망 기반 지표 파라미터 최적화 모델"""
    def __init__(self, input_size = 30, hidden_size = 64):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.out = nn.Linear(hidden_size, 6) #RSI, MACD fast MACD Slow, Bollinger Band window, Bollinger Band std)

    def forward(self, x):
        """Tensor shape(batch, input size)"""
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = torch.sigmoid(self.out(x)) # 0~1 output
        return x

# mapping NN outputs to indicator parameter(int or float)
    def map_to_params(self, normalized_output):
        """
        convert 0~1 output to real indicator parameter
        normalized _output : Tensor shape(batch, 6)
        returns: dict of parameters
        """
        o = normalized_output.detach().cpu().flatten().tolist()

        # (name, min, max, is_int)
        params_config = [
            ("rsi_period", 5, 30, True),
            ("macd_fast", 5, 20, True),
            ("macd_slow", 15, 40, True),
            ("macd_signal", 5, 20, True),
            ("bollinger_bands_window", 10, 40, True),
            ("bollinger_bands_std", 1, 3, False)
        ]
          
        params = {}

        for i, (name, min_value, max_value, is_int) in enumerate(params_config):
            val = min_value + o[i] * (max_value - min_value)
            params[name] = int(val) if is_int else float(val)

        return params
    
"""
Quick test(run this file directly)
"""

if __name__ == "__main__":
    model = IndicatorParamNN()

    # fake market feature(30 days returns)
    sample_input = torch.randn(1,30)

    print("sample input: ", sample_input)

    output = model(sample_input)
    print("normalized output : ", output)

    real_params = model.map_to_params(output)
    print("mapped parameters:", real_params)


