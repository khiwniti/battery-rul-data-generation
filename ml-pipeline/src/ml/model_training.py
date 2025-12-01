"""
Model Training Module
Train CatBoost model for RUL prediction
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ..core.config import settings

logger = logging.getLogger(__name__)


class RULModelTrainer:
    """Train and evaluate RUL prediction model"""

    def __init__(
        self,
        iterations: int = None,
        learning_rate: float = None,
        depth: int = None,
        l2_leaf_reg: float = None
    ):
        """
        Initialize model trainer

        Args:
            iterations: Number of boosting iterations
            learning_rate: Learning rate
            depth: Tree depth
            l2_leaf_reg: L2 regularization
        """
        self.iterations = iterations or settings.CATBOOST_ITERATIONS
        self.learning_rate = learning_rate or settings.CATBOOST_LEARNING_RATE
        self.depth = depth or settings.CATBOOST_DEPTH
        self.l2_leaf_reg = l2_leaf_reg or settings.CATBOOST_L2_LEAF_REG

        self.model: Optional[CatBoostRegressor] = None
        self.feature_names: Optional[list] = None
        self.training_metrics: Optional[Dict] = None

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict:
        """
        Train CatBoost model

        Args:
            X: Feature matrix
            y: Target variable (RUL in days)
            test_size: Proportion of data for testing
            random_state: Random seed

        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training RUL model on {len(X)} samples")

        # Store feature names
        self.feature_names = list(X.columns)

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

        # Create CatBoost datasets
        train_pool = Pool(X_train, y_train)
        test_pool = Pool(X_test, y_test)

        # Initialize model
        self.model = CatBoostRegressor(
            iterations=self.iterations,
            learning_rate=self.learning_rate,
            depth=self.depth,
            l2_leaf_reg=self.l2_leaf_reg,
            loss_function='RMSE',
            eval_metric='RMSE',
            random_seed=random_state,
            verbose=100,  # Print every 100 iterations
            early_stopping_rounds=50,
        )

        # Train
        self.model.fit(
            train_pool,
            eval_set=test_pool,
            use_best_model=True,
        )

        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)

        metrics = {
            'train': {
                'mae': float(mean_absolute_error(y_train, y_pred_train)),
                'rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
                'r2': float(r2_score(y_train, y_pred_train)),
            },
            'test': {
                'mae': float(mean_absolute_error(y_test, y_pred_test)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
                'r2': float(r2_score(y_test, y_pred_test)),
            },
            'feature_importance': self._get_feature_importance(),
            'model_params': {
                'iterations': self.iterations,
                'learning_rate': self.learning_rate,
                'depth': self.depth,
                'l2_leaf_reg': self.l2_leaf_reg,
            },
            'training_samples': len(X_train),
            'test_samples': len(X_test),
        }

        self.training_metrics = metrics

        logger.info(f"Training complete - Test MAE: {metrics['test']['mae']:.2f} days, R²: {metrics['test']['r2']:.3f}")

        return metrics

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if self.model is None or self.feature_names is None:
            return {}

        importance = self.model.get_feature_importance()
        return {
            name: float(imp)
            for name, imp in zip(self.feature_names, importance)
        }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make RUL predictions

        Args:
            X: Feature matrix

        Returns:
            Array of RUL predictions in days
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict(X)

    def predict_with_confidence(
        self,
        X: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make RUL predictions with confidence estimates

        Args:
            X: Feature matrix

        Returns:
            Tuple of (predictions, confidence_scores)
        """
        predictions = self.predict(X)

        # Estimate confidence based on prediction uncertainty
        # Using virtual ensembles in CatBoost
        if hasattr(self.model, 'virtual_ensembles_predict'):
            # Get predictions from multiple virtual ensembles
            ensemble_predictions = []
            for i in range(0, self.model.tree_count_, max(1, self.model.tree_count_ // 10)):
                pred = self.model.predict(X, ntree_end=i + 1)
                ensemble_predictions.append(pred)

            ensemble_predictions = np.array(ensemble_predictions)
            std_dev = np.std(ensemble_predictions, axis=0)

            # Convert std_dev to confidence score (0-1)
            # Lower std_dev = higher confidence
            confidence = 1.0 / (1.0 + std_dev / (predictions + 1))
        else:
            # Fallback: uniform confidence
            confidence = np.full(len(predictions), 0.8)

        return predictions, confidence

    def save_model(self, model_path: Optional[Path] = None) -> Path:
        """
        Save trained model to disk

        Args:
            model_path: Path to save model (default: settings.MODEL_PATH)

        Returns:
            Path where model was saved
        """
        if self.model is None:
            raise ValueError("No model to save. Train a model first.")

        model_path = model_path or settings.MODEL_PATH
        model_path.parent.mkdir(parents=True, exist_ok=True)

        # Save CatBoost model
        self.model.save_model(str(model_path))

        # Save feature names and metadata
        metadata = {
            'feature_names': self.feature_names,
            'training_metrics': self.training_metrics,
            'model_params': {
                'iterations': self.iterations,
                'learning_rate': self.learning_rate,
                'depth': self.depth,
                'l2_leaf_reg': self.l2_leaf_reg,
            }
        }

        metadata_path = model_path.parent / 'model_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model saved to {model_path}")
        logger.info(f"Metadata saved to {metadata_path}")

        return model_path

    def load_model(self, model_path: Optional[Path] = None) -> None:
        """
        Load trained model from disk

        Args:
            model_path: Path to load model from (default: settings.MODEL_PATH)
        """
        model_path = model_path or settings.MODEL_PATH

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Load CatBoost model
        self.model = CatBoostRegressor()
        self.model.load_model(str(model_path))

        # Load metadata
        metadata_path = model_path.parent / 'model_metadata.json'
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            self.feature_names = metadata.get('feature_names')
            self.training_metrics = metadata.get('training_metrics')

        logger.info(f"Model loaded from {model_path}")

    @property
    def is_trained(self) -> bool:
        """Check if model is trained"""
        return self.model is not None
