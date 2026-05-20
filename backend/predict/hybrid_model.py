# -*- coding: utf-8 -*-
"""
LSTM + LightGBM 混合模型
采用堆叠集成（Stacking）架构
支持 Walk-Forward 交叉验证

@author: StockQuant Team
@date: 2026-05-20
"""

import numpy as np
import logging
import warnings
from typing import Tuple, Dict, Any, Optional, List
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# 忽略 LightGBM 特征名称警告（numpy 数组输入时无列名，属于正常行为）
warnings.filterwarnings('ignore', message='.*does not have valid feature names.*')

logger = logging.getLogger(__name__)

# 尝试导入 torch（可选依赖）
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch 未安装，将使用纯 LightGBM 模型")

# 尝试导入 LightGBM
try:
    from lightgbm import LGBMClassifier, LGBMRegressor
    LGBM_AVAILABLE = True
except ImportError:
    LGBM_AVAILABLE = False
    logger.warning("LightGBM 未安装")


class LSTMModel(nn.Module):
    """
    LSTM 子模型 - 提取时序特征
    
    双向 LSTM，用于捕捉价格序列中的长短期依赖关系
    """
    
    def __init__(self, input_size: int, hidden_size: int = 128, 
                 num_layers: int = 2, dropout: float = 0.2):
        """
        Args:
            input_size: 输入特征维度
            hidden_size: LSTM 隐藏层维度
            num_layers: LSTM 层数
            dropout: Dropout 比例
        """
        super(LSTMModel, self).__init__()
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size * 2, 64)  # *2 因为双向
        self.relu = nn.ReLU()
        self.output = nn.Linear(64, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        lstm_out, _ = self.lstm(x)
        last_out = lstm_out[:, -1, :]
        features = self.relu(self.fc(self.dropout(last_out)))
        output = self.sigmoid(self.output(features))
        return output
    
    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """提取中间层特征（用于堆叠集成）"""
        with torch.no_grad():
            lstm_out, _ = self.lstm(x)
            last_out = lstm_out[:, -1, :]
            features = self.relu(self.fc(last_out))
        return features


class LSTMLightGBMHybrid:
    """
    LSTM + LightGBM 混合模型（堆叠集成）
    
    架构：
    1. LSTM 提取时序特征
    2. LightGBM 处理结构化特征
    3. 元模型合并两者的输出
    """
    
    def __init__(self, seq_length: int = 20, lstm_input_dim: int = 10,
                 lstm_hidden: int = 128, lstm_layers: int = 2,
                 lstm_dropout: float = 0.2, use_lstm: bool = True):
        """
        Args:
            seq_length: LSTM 回看窗口长度
            lstm_input_dim: LSTM 输入特征维度
            lstm_hidden: LSTM 隐藏层维度
            lstm_layers: LSTM 层数
            lstm_dropout: Dropout 比例
            use_lstm: 是否使用 LSTM（如果 PyTorch 未安装则自动禁用）
        """
        self.seq_length = seq_length
        self.lstm_input_dim = lstm_input_dim
        self.lstm_hidden = lstm_hidden
        self.lstm_layers = lstm_layers
        self.lstm_dropout = lstm_dropout
        self.use_lstm = use_lstm and TORCH_AVAILABLE
        
        self.lstm_model: Optional[LSTMModel] = None
        self.lgb_model: Optional['LGBMClassifier'] = None
        self.meta_model: Optional['LGBMClassifier'] = None
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 初始化模型
        self._init_models()
    
    def _init_models(self):
        """初始化所有子模型"""
        if self.use_lstm:
            self.lstm_model = LSTMModel(
                input_size=self.lstm_input_dim,
                hidden_size=self.lstm_hidden,
                num_layers=self.lstm_layers,
                dropout=self.lstm_dropout
            )
        
        # LightGBM 模型
        self.lgb_model = LGBMClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=7,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=0.1,
            random_state=42,
            verbose=-1
        )
        
        # 元模型
        if self.use_lstm:
            self.meta_model = LGBMClassifier(
                n_estimators=50,
                learning_rate=0.03,
                max_depth=3,
                random_state=42,
                verbose=-1
            )
    
    def _train_lstm(self, X_lstm: np.ndarray, y: np.ndarray, 
                    epochs: int = 50, batch_size: int = 32, 
                    lr: float = 0.001,
                    validation_data: Optional[Tuple[np.ndarray, np.ndarray]] = None) -> Dict[str, List[float]]:
        """
        训练 LSTM 模型
        
        Args:
            X_lstm: LSTM 输入数据 (samples, seq_len, features)
            y: 目标标签
            epochs: 训练轮数
            batch_size: 批次大小
            lr: 学习率
            validation_data: 验证数据 (X_val, y_val)
            
        Returns:
            训练历史 {'train_loss': [...], 'val_loss': [...]}
        """
        history = {'train_loss': [], 'val_loss': []}
        
        if not self.use_lstm or self.lstm_model is None:
            return history
        
        self.lstm_model = self.lstm_model.to(self.device)
        self.lstm_model.train()
        
        # 转换为 PyTorch 张量
        X_tensor = torch.FloatTensor(X_lstm).to(self.device)
        y_tensor = torch.FloatTensor(y).unsqueeze(1).to(self.device)
        
        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        optimizer = optim.Adam(self.lstm_model.parameters(), lr=lr)
        criterion = nn.BCELoss()
        
        for epoch in range(epochs):
            total_loss = 0
            self.lstm_model.train()
            
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                outputs = self.lstm_model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            
            avg_loss = total_loss / len(dataloader)
            history['train_loss'].append(avg_loss)
            
            # 验证集评估
            if validation_data is not None:
                self.lstm_model.eval()
                X_val, y_val = validation_data
                X_val_tensor = torch.FloatTensor(X_val).to(self.device)
                y_val_tensor = torch.FloatTensor(y_val).unsqueeze(1).to(self.device)
                
                with torch.no_grad():
                    val_outputs = self.lstm_model(X_val_tensor)
                    val_loss = criterion(val_outputs, y_val_tensor).item()
                    history['val_loss'].append(val_loss)
            
            if (epoch + 1) % 10 == 0:
                val_str = f", Val Loss: {history['val_loss'][-1]:.4f}" if validation_data else ""
                logger.info(f"LSTM Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}{val_str}")
        
        return history
    
    def _extract_lstm_features(self, X_lstm: np.ndarray) -> np.ndarray:
        """提取 LSTM 的中间层特征"""
        if not self.use_lstm or self.lstm_model is None:
            return np.zeros((len(X_lstm), 64))
        
        self.lstm_model.eval()
        X_tensor = torch.FloatTensor(X_lstm).to(self.device)
        
        features = []
        with torch.no_grad():
            batch_size = 64
            for i in range(0, len(X_tensor), batch_size):
                batch = X_tensor[i:i+batch_size]
                batch_features = self.lstm_model.extract_features(batch)
                features.append(batch_features.cpu().numpy())
        
        return np.concatenate(features, axis=0)
    
    def train(self, X_lstm: np.ndarray, X_lgb: np.ndarray, y: np.ndarray,
              lstm_epochs: int = 50, lstm_batch_size: int = 32, lstm_lr: float = 0.001,
              validation_split: float = 0.2) -> 'LSTMLightGBMHybrid':
        """
        训练混合模型
        
        Args:
            X_lstm: LSTM 输入数据 (samples, seq_len, features)
            X_lgb: LightGBM 输入数据 (samples, n_features)
            y: 目标标签
            lstm_epochs: LSTM 训练轮数
            lstm_batch_size: LSTM 批次大小
            lstm_lr: LSTM 学习率
            validation_split: 验证集比例
        """
        # 划分验证集
        split_idx = int(len(y) * (1 - validation_split))
        
        if self.use_lstm:
            logger.info("训练 LSTM...")
            self._train_lstm(
                X_lstm[:split_idx], y[:split_idx],
                epochs=lstm_epochs,
                batch_size=lstm_batch_size,
                lr=lstm_lr,
                validation_data=(X_lstm[split_idx:], y[split_idx:])
            )
            
            logger.info("提取 LSTM 特征...")
            lstm_features = self._extract_lstm_features(X_lstm)
        else:
            lstm_features = np.zeros((len(X_lgb), 64))
        
        logger.info("训练 LightGBM...")
        # 转换为 numpy 数组以避免 sklearn 特征名称警告
        X_lgb_np = np.asarray(X_lgb, dtype=np.float64)
        y_np = np.asarray(y, dtype=np.int32)
        self.lgb_model.fit(X_lgb_np, y_np)
        lgb_proba = self.lgb_model.predict_proba(X_lgb_np)[:, 1]
        
        if self.use_lstm and self.meta_model is not None:
            logger.info("训练元模型（堆叠层）...")
            meta_X = np.column_stack([lstm_features, lgb_proba])
            self.meta_model.fit(meta_X, y_np)
        
        logger.info("混合模型训练完成！")
        return self
    
    def predict(self, X_lstm: np.ndarray, X_lgb: np.ndarray) -> np.ndarray:
        """预测"""
        # 确保输入为 numpy 数组
        X_lgb_np = np.asarray(X_lgb, dtype=np.float64)
        
        if self.use_lstm and self.meta_model is not None:
            lstm_features = self._extract_lstm_features(X_lstm)
            lgb_proba = self.lgb_model.predict_proba(X_lgb_np)[:, 1]
            meta_X = np.column_stack([lstm_features, lgb_proba])
            proba = self.meta_model.predict_proba(meta_X)[:, 1]
        else:
            proba = self.lgb_model.predict_proba(X_lgb_np)[:, 1]
        
        return proba
    
    def predict_class(self, X_lstm: np.ndarray, X_lgb: np.ndarray, 
                      threshold: float = 0.5) -> np.ndarray:
        """预测类别"""
        proba = self.predict(X_lstm, X_lgb)
        return (proba > threshold).astype(int)
    
    def evaluate(self, X_lstm: np.ndarray, X_lgb: np.ndarray, 
                 y_test: np.ndarray) -> Dict[str, float]:
        """评估模型性能"""
        pred_proba = self.predict(X_lstm, X_lgb)
        pred_class = (pred_proba > 0.5).astype(int)
        
        try:
            auc = roc_auc_score(y_test, pred_proba)
        except:
            auc = 0.0
        
        return {
            'accuracy': accuracy_score(y_test, pred_class),
            'precision': precision_score(y_test, pred_class, zero_division=0),
            'recall': recall_score(y_test, pred_class, zero_division=0),
            'f1': f1_score(y_test, pred_class, zero_division=0),
            'auc': auc
        }
    
    def save(self, dir_path: str = './models/hybrid') -> Dict[str, str]:
        """保存模型"""
        import os
        import joblib
        
        os.makedirs(dir_path, exist_ok=True)
        saved_files = {}
        
        if self.use_lstm and self.lstm_model is not None:
            lstm_path = f'{dir_path}/lstm_model.pth'
            torch.save(self.lstm_model.state_dict(), lstm_path)
            saved_files['lstm'] = lstm_path
        
        if self.lgb_model is not None:
            lgb_path = f'{dir_path}/lgb_model.pkl'
            joblib.dump(self.lgb_model, lgb_path)
            saved_files['lightgbm'] = lgb_path
        
        if self.meta_model is not None:
            meta_path = f'{dir_path}/meta_model.pkl'
            joblib.dump(self.meta_model, meta_path)
            saved_files['meta'] = meta_path
        
        # 保存模型参数
        config_path = f'{dir_path}/model_config.json'
        import json
        config = {
            'seq_length': self.seq_length,
            'lstm_input_dim': self.lstm_input_dim,
            'lstm_hidden': self.lstm_hidden,
            'lstm_layers': self.lstm_layers,
            'lstm_dropout': self.lstm_dropout,
            'use_lstm': self.use_lstm
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        saved_files['config'] = config_path
        
        logger.info(f"模型已保存到: {dir_path}")
        return saved_files
    
    def load(self, dir_path: str = './models/hybrid') -> 'LSTMLightGBMHybrid':
        """加载模型"""
        import os
        import joblib
        import json
        
        if self.use_lstm and self.lstm_model is not None and os.path.exists(f'{dir_path}/lstm_model.pth'):
            self.lstm_model.load_state_dict(
                torch.load(f'{dir_path}/lstm_model.pth', map_location=self.device, weights_only=True)
            )
            self.lstm_model = self.lstm_model.to(self.device)
        
        if os.path.exists(f'{dir_path}/lgb_model.pkl'):
            self.lgb_model = joblib.load(f'{dir_path}/lgb_model.pkl')
        
        if os.path.exists(f'{dir_path}/meta_model.pkl'):
            self.meta_model = joblib.load(f'{dir_path}/meta_model.pkl')
        
        # 加载配置
        config_path = f'{dir_path}/model_config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.seq_length = config.get('seq_length', self.seq_length)
                self.lstm_input_dim = config.get('lstm_input_dim', self.lstm_input_dim)
        
        logger.info(f"模型已加载: {dir_path}")
        return self
    
    def get_feature_importance(self, X_lgb: np.ndarray) -> np.ndarray:
        """获取 LightGBM 特征重要性"""
        if self.lgb_model is not None:
            return self.lgb_model.feature_importances_
        return np.zeros(X_lgb.shape[1])


def walk_forward_validation(X_lstm: np.ndarray, X_lgb: np.ndarray, y: np.ndarray,
                            seq_length: int, lstm_input_dim: int,
                            train_window: int = 200, test_window: int = 20,
                            lstm_epochs: int = 30, lstm_hidden: int = 128,
                            lgb_n_estimators: int = 100, learning_rate: float = 0.05) -> Dict[str, Any]:
    """
    Walk-Forward 交叉验证
    
    模拟真实交易环境：
    1. 使用历史窗口训练模型
    2. 在未来窗口测试
    3. 滚动窗口重复
    
    Args:
        X_lstm: LSTM 输入数据
        X_lgb: LightGBM 输入数据
        y: 目标标签
        seq_length: LSTM 回看窗口
        lstm_input_dim: LSTM 输入维度
        train_window: 训练窗口大小
        test_window: 测试窗口大小
        lstm_epochs: LSTM 训练轮数
        lstm_hidden: LSTM 隐藏层大小
        lgb_n_estimators: LightGBM 树数量
        learning_rate: 学习率
    
    Returns:
        验证结果字典
    """
    results = []
    total_samples = len(y)
    current_idx = train_window
    
    logger.info(f"开始 Walk-Forward 验证: 总样本={total_samples}, 训练窗口={train_window}, 测试窗口={test_window}")
    
    while current_idx + test_window <= total_samples:
        # 训练集
        train_end = current_idx
        train_start = max(0, train_end - train_window)
        
        # 测试集
        test_start = train_end
        test_end = min(train_end + test_window, total_samples)
        
        if test_end - test_start < 5:
            break
        
        # 划分数据
        X_lstm_train = X_lstm[train_start:train_end]
        X_lgb_train = X_lgb[train_start:train_end]
        y_train = y[train_start:train_end]
        
        X_lstm_test = X_lstm[test_start:test_end]
        X_lgb_test = X_lgb[test_start:test_end]
        y_test = y[test_start:test_end]
        
        if len(y_train) < 50 or len(y_test) < 5:
            current_idx += test_window
            continue
        
        try:
            # 创建并训练模型
            model = LSTMLightGBMHybrid(
                seq_length=seq_length,
                lstm_input_dim=lstm_input_dim,
                lstm_hidden=lstm_hidden,
                use_lstm=TORCH_AVAILABLE
            )
            
            # 更新 LightGBM 参数
            model.lgb_model = LGBMClassifier(
                n_estimators=lgb_n_estimators,
                learning_rate=learning_rate,
                max_depth=7,
                random_state=42,
                verbose=-1
            )
            
            model.train(
                X_lstm_train, X_lgb_train, y_train,
                lstm_epochs=lstm_epochs,
                validation_split=0.1
            )
            
            # 评估
            metrics = model.evaluate(X_lstm_test, X_lgb_test, y_test)
            metrics['train_start'] = train_start
            metrics['train_end'] = train_end
            metrics['test_start'] = test_start
            metrics['test_end'] = test_end
            metrics['train_samples'] = len(y_train)
            metrics['test_samples'] = len(y_test)
            
            results.append(metrics)
            logger.info(f"窗口 [{test_start}-{test_end}]: Acc={metrics['accuracy']:.3f}, F1={metrics['f1']:.3f}, AUC={metrics['auc']:.3f}")
            
        except Exception as e:
            logger.warning(f"窗口 [{test_start}-{test_end}] 训练失败: {e}")
        
        current_idx += test_window
    
    # 汇总结果
    if not results:
        return {'error': '验证失败，无有效结果'}
    
    accs = [r['accuracy'] for r in results]
    f1s = [r['f1'] for r in results]
    aucs = [r['auc'] for r in results]
    
    return {
        'windows': len(results),
        'avg_accuracy': float(np.mean(accs)),
        'std_accuracy': float(np.std(accs)),
        'avg_f1': float(np.mean(f1s)),
        'std_f1': float(np.std(f1s)),
        'avg_auc': float(np.mean(aucs)),
        'std_auc': float(np.std(aucs)),
        'max_accuracy': float(np.max(accs)),
        'min_accuracy': float(np.min(accs)),
        'window_results': results
    }
