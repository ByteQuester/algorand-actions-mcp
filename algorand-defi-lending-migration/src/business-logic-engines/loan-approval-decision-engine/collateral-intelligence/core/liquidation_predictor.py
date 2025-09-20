"""
Advanced Liquidation Risk Prediction Engine

ML-based liquidation risk prediction using sophisticated models to forecast
liquidation probability across different time horizons.
"""

import numpy as np
import pandas as pd
import yaml
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from pathlib import Path
import sqlite3
import json
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, precision_recall_curve
import joblib
import warnings
warnings.filterwarnings('ignore')

@dataclass
class LiquidationPrediction:
    """Individual liquidation prediction result"""
    asset_symbol: str
    prediction_horizon: str  # short_term, medium_term, long_term
    liquidation_probability: float
    confidence_interval: Tuple[float, float]
    risk_level: str
    contributing_factors: Dict[str, float]
    model_confidence: float

@dataclass
class PortfolioLiquidationRisk:
    """Portfolio-level liquidation risk assessment"""
    overall_liquidation_probability: float
    worst_case_scenario_probability: float
    expected_liquidation_value: float
    time_to_liquidation_estimate: Optional[int]  # days
    cascade_risk_probability: float
    stress_test_results: Dict[str, float]

@dataclass
class LiquidationFeatures:
    """Feature set for liquidation prediction"""
    # Price-based features
    price_volatility: float
    price_momentum: float
    price_trend: float
    relative_strength_index: float
    bollinger_position: float

    # Volume-based features
    volume_trend: float
    volume_volatility: float
    volume_price_divergence: float
    liquidity_ratio: float

    # Market structure features
    market_cap: float
    trading_pairs: int
    exchange_concentration: float
    order_book_depth: float

    # Correlation features
    market_correlation: float
    sector_correlation: float
    systematic_risk_exposure: float

    # Macro features
    market_sentiment: float
    volatility_index: float
    funding_rates: float

@dataclass
class LiquidationPredictionAnalysis:
    """Complete liquidation prediction analysis"""
    address: str
    analysis_timestamp: datetime
    asset_predictions: List[LiquidationPrediction]
    portfolio_risk: PortfolioLiquidationRisk
    prediction_model_performance: Dict[str, float]
    feature_importance: Dict[str, float]
    risk_mitigation_strategies: List[str]
    early_warning_indicators: List[str]
    confidence_level: float

class LiquidationPredictor:
    """Advanced ML-based liquidation risk predictor"""

    def __init__(self, config_path: str = None):
        """Initialize the liquidation predictor"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.liquidation_config = self.config['liquidation_prediction']
        self.ml_config = self.config['ml_configuration']

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize models
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}

        # Initialize database
        self._init_database()

        # Load or train models
        self._initialize_models()

    def _init_database(self):
        """Initialize database for liquidation prediction data"""
        db_path = self.config['database']['model_storage_db']
        self.db_path = db_path

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Liquidation events table (for training data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS liquidation_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_symbol TEXT NOT NULL,
                    liquidation_date DATETIME NOT NULL,
                    pre_liquidation_features TEXT NOT NULL,
                    liquidation_value REAL,
                    liquidation_cause TEXT,
                    time_to_liquidation_days INTEGER
                )
            """)

            # Predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS liquidation_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT NOT NULL,
                    asset_symbol TEXT NOT NULL,
                    prediction_date DATETIME NOT NULL,
                    horizon TEXT NOT NULL,
                    probability REAL NOT NULL,
                    confidence REAL NOT NULL,
                    features TEXT NOT NULL
                )
            """)

            # Model performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    training_date DATETIME NOT NULL,
                    validation_auc REAL,
                    cross_val_score REAL,
                    feature_count INTEGER,
                    training_samples INTEGER
                )
            """)

            conn.commit()

    def _initialize_models(self):
        """Initialize or load ML models"""
        try:
            # Try to load existing models
            self._load_models()
        except:
            self.logger.info("No existing models found, initializing new models")
            self._create_default_models()

        # Generate synthetic training data if needed
        if not self._has_sufficient_training_data():
            self.logger.info("Generating synthetic training data")
            self._generate_synthetic_training_data()

    def _load_models(self):
        """Load pre-trained models"""
        model_dir = Path(__file__).parent.parent / "models"
        model_dir.mkdir(exist_ok=True)

        horizons = ['short_term', 'medium_term', 'long_term']

        for horizon in horizons:
            try:
                model_path = model_dir / f"liquidation_model_{horizon}.joblib"
                scaler_path = model_dir / f"scaler_{horizon}.joblib"

                if model_path.exists() and scaler_path.exists():
                    self.models[horizon] = joblib.load(model_path)
                    self.scalers[horizon] = joblib.load(scaler_path)
                    self.logger.info(f"Loaded model for {horizon}")
                else:
                    raise FileNotFoundError(f"Model files not found for {horizon}")

            except Exception as e:
                self.logger.warning(f"Could not load model for {horizon}: {str(e)}")
                self._create_model_for_horizon(horizon)

    def _create_default_models(self):
        """Create default ML models"""
        horizons = ['short_term', 'medium_term', 'long_term']

        for horizon in horizons:
            self._create_model_for_horizon(horizon)

    def _create_model_for_horizon(self, horizon: str):
        """Create ML model for specific time horizon"""
        primary_model = self.liquidation_config['ml_models']['primary_model']

        if primary_model == 'gradient_boosting':
            model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
        else:  # random_forest fallback
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )

        self.models[horizon] = model
        self.scalers[horizon] = StandardScaler()

        self.logger.info(f"Created {primary_model} model for {horizon}")

    def _has_sufficient_training_data(self) -> bool:
        """Check if we have sufficient training data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM liquidation_events")
            count = cursor.fetchone()[0]

        minimum_samples = self.ml_config['training_data']['minimum_observations']
        return count >= minimum_samples

    def _generate_synthetic_training_data(self):
        """Generate synthetic training data for model development"""
        np.random.seed(42)

        # Generate synthetic liquidation events
        n_samples = 1000
        assets = ['ALGO', 'USDC', 'BTC', 'ETH', 'ASA1', 'ASA2']

        for i in range(n_samples):
            asset = np.random.choice(assets)
            liquidation_date = datetime.now() - timedelta(days=np.random.randint(1, 730))

            # Generate synthetic features that lead to liquidation
            features = self._generate_synthetic_features(is_liquidation=True)

            # Add some non-liquidation events
            if i % 3 == 0:  # 1/3 are non-liquidation events
                features = self._generate_synthetic_features(is_liquidation=False)
                liquidation_value = 0
                time_to_liquidation = None
            else:
                liquidation_value = np.random.uniform(1000, 100000)
                time_to_liquidation = np.random.randint(1, 30)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO liquidation_events
                    (asset_symbol, liquidation_date, pre_liquidation_features,
                     liquidation_value, liquidation_cause, time_to_liquidation_days)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    asset,
                    liquidation_date,
                    json.dumps(features),
                    liquidation_value,
                    "synthetic_volatility" if liquidation_value > 0 else "no_liquidation",
                    time_to_liquidation
                ))
                conn.commit()

        self.logger.info(f"Generated {n_samples} synthetic training samples")

    def _generate_synthetic_features(self, is_liquidation: bool) -> Dict:
        """Generate synthetic feature set"""
        if is_liquidation:
            # Features that typically lead to liquidation
            return {
                'price_volatility': np.random.uniform(0.6, 1.0),
                'price_momentum': np.random.uniform(-0.8, -0.2),
                'volume_trend': np.random.uniform(-0.6, 0.2),
                'market_correlation': np.random.uniform(0.7, 1.0),
                'liquidity_ratio': np.random.uniform(0.1, 0.4),
                'market_sentiment': np.random.uniform(-0.8, -0.2),
                'volatility_index': np.random.uniform(0.6, 1.0),
                'relative_strength_index': np.random.uniform(0.1, 0.3),
                'bollinger_position': np.random.uniform(-1.0, -0.5)
            }
        else:
            # Features for stable conditions
            return {
                'price_volatility': np.random.uniform(0.1, 0.4),
                'price_momentum': np.random.uniform(-0.2, 0.3),
                'volume_trend': np.random.uniform(-0.2, 0.4),
                'market_correlation': np.random.uniform(0.2, 0.6),
                'liquidity_ratio': np.random.uniform(0.5, 1.0),
                'market_sentiment': np.random.uniform(-0.2, 0.8),
                'volatility_index': np.random.uniform(0.1, 0.4),
                'relative_strength_index': np.random.uniform(0.4, 0.8),
                'bollinger_position': np.random.uniform(-0.3, 0.3)
            }

    async def predict_liquidation_risk(self,
                                     collateral_assets: List[Dict[str, Any]],
                                     borrower_profile: Dict[str, Any] = None,
                                     market_conditions: Dict[str, Any] = None) -> LiquidationPredictionAnalysis:
        """
        Comprehensive liquidation risk prediction

        Args:
            collateral_assets: List of collateral assets
            borrower_profile: Borrower behavior profile
            market_conditions: Current market conditions

        Returns:
            LiquidationPredictionAnalysis with predictions
        """
        try:
            self.logger.info("Starting liquidation risk prediction")

            # Ensure models are trained
            await self._ensure_models_trained()

            # Generate predictions for each asset
            asset_predictions = []
            for asset in collateral_assets:
                predictions = await self._predict_asset_liquidation_risk(
                    asset, borrower_profile, market_conditions
                )
                asset_predictions.extend(predictions)

            # Calculate portfolio-level risk
            portfolio_risk = self._calculate_portfolio_liquidation_risk(
                asset_predictions, collateral_assets
            )

            # Get model performance metrics
            model_performance = self._get_model_performance_metrics()

            # Calculate feature importance
            feature_importance = self._calculate_feature_importance()

            # Generate risk mitigation strategies
            mitigation_strategies = self._generate_risk_mitigation_strategies(
                asset_predictions, portfolio_risk
            )

            # Identify early warning indicators
            early_warnings = self._identify_early_warning_indicators(
                asset_predictions, portfolio_risk
            )

            # Calculate confidence level
            confidence_level = self._calculate_prediction_confidence(
                asset_predictions, model_performance
            )

            analysis = LiquidationPredictionAnalysis(
                address=borrower_profile.get('address', 'unknown') if borrower_profile else 'unknown',
                analysis_timestamp=datetime.now(),
                asset_predictions=asset_predictions,
                portfolio_risk=portfolio_risk,
                prediction_model_performance=model_performance,
                feature_importance=feature_importance,
                risk_mitigation_strategies=mitigation_strategies,
                early_warning_indicators=early_warnings,
                confidence_level=confidence_level
            )

            # Store predictions
            await self._store_predictions(analysis)

            self.logger.info("Liquidation risk prediction completed successfully")
            return analysis

        except Exception as e:
            self.logger.error(f"Error in liquidation risk prediction: {str(e)}")
            raise

    async def _ensure_models_trained(self):
        """Ensure all models are properly trained"""
        for horizon in ['short_term', 'medium_term', 'long_term']:
            if horizon not in self.models or not hasattr(self.models[horizon], 'predict'):
                await self._train_model_for_horizon(horizon)

    async def _train_model_for_horizon(self, horizon: str):
        """Train model for specific time horizon"""
        try:
            self.logger.info(f"Training model for {horizon}")

            # Get training data
            X, y = self._prepare_training_data(horizon)

            if len(X) < 10:  # Not enough data
                self.logger.warning(f"Insufficient training data for {horizon}, using default model")
                return

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            model = self.models[horizon]
            model.fit(X_train_scaled, y_train)

            # Evaluate model
            train_score = model.score(X_train_scaled, y_train)
            test_score = model.score(X_test_scaled, y_test)
            cross_val = cross_val_score(model, X_train_scaled, y_train, cv=3).mean()

            # Store scaler and update model
            self.scalers[horizon] = scaler
            self.models[horizon] = model

            # Store performance metrics
            self._store_model_performance(horizon, test_score, cross_val, len(X_train))

            self.logger.info(f"Model trained for {horizon}: train={train_score:.3f}, test={test_score:.3f}, cv={cross_val:.3f}")

        except Exception as e:
            self.logger.error(f"Error training model for {horizon}: {str(e)}")

    def _prepare_training_data(self, horizon: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for specific horizon"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT pre_liquidation_features,
                       CASE WHEN liquidation_value > 0 THEN 1 ELSE 0 END as is_liquidation
                FROM liquidation_events
                WHERE time_to_liquidation_days IS NULL OR time_to_liquidation_days <= ?
            """

            # Adjust time threshold based on horizon
            time_thresholds = {
                'short_term': self.liquidation_config['prediction_horizons']['short_term'],
                'medium_term': self.liquidation_config['prediction_horizons']['medium_term'],
                'long_term': self.liquidation_config['prediction_horizons']['long_term']
            }

            threshold = time_thresholds[horizon]
            df = pd.read_sql_query(query, conn, params=[threshold])

        if df.empty:
            return np.array([]), np.array([])

        # Extract features
        features_list = []
        labels = []

        for _, row in df.iterrows():
            try:
                features_dict = json.loads(row['pre_liquidation_features'])
                features_vector = [
                    features_dict.get('price_volatility', 0),
                    features_dict.get('price_momentum', 0),
                    features_dict.get('volume_trend', 0),
                    features_dict.get('market_correlation', 0),
                    features_dict.get('liquidity_ratio', 0),
                    features_dict.get('market_sentiment', 0),
                    features_dict.get('volatility_index', 0),
                    features_dict.get('relative_strength_index', 0),
                    features_dict.get('bollinger_position', 0)
                ]
                features_list.append(features_vector)
                labels.append(row['is_liquidation'])
            except:
                continue

        return np.array(features_list), np.array(labels)

    async def _predict_asset_liquidation_risk(self,
                                            asset: Dict[str, Any],
                                            borrower_profile: Dict[str, Any],
                                            market_conditions: Dict[str, Any]) -> List[LiquidationPrediction]:
        """Predict liquidation risk for a single asset across all horizons"""
        predictions = []

        # Extract features for the asset
        features = await self._extract_asset_features(asset, market_conditions)

        for horizon in ['short_term', 'medium_term', 'long_term']:
            try:
                # Get model and scaler
                model = self.models.get(horizon)
                scaler = self.scalers.get(horizon)

                if not model or not scaler:
                    self.logger.warning(f"No model available for {horizon}")
                    continue

                # Prepare feature vector
                feature_vector = self._features_to_vector(features)
                feature_vector_scaled = scaler.transform([feature_vector])

                # Make prediction
                probability = model.predict_proba(feature_vector_scaled)[0][1]  # Probability of liquidation

                # Calculate confidence interval (simplified)
                confidence_interval = (
                    max(0, probability - 0.1),
                    min(1, probability + 0.1)
                )

                # Determine risk level
                risk_level = self._probability_to_risk_level(probability)

                # Calculate contributing factors
                contributing_factors = self._calculate_contributing_factors(
                    features, model, feature_vector_scaled
                )

                # Model confidence (based on training performance)
                model_confidence = self._get_model_confidence(horizon)

                prediction = LiquidationPrediction(
                    asset_symbol=asset.get('symbol', 'UNKNOWN'),
                    prediction_horizon=horizon,
                    liquidation_probability=round(probability, 3),
                    confidence_interval=confidence_interval,
                    risk_level=risk_level,
                    contributing_factors=contributing_factors,
                    model_confidence=model_confidence
                )

                predictions.append(prediction)

            except Exception as e:
                self.logger.error(f"Error predicting for {asset.get('symbol')} {horizon}: {str(e)}")

        return predictions

    async def _extract_asset_features(self, asset: Dict[str, Any], market_conditions: Dict[str, Any]) -> LiquidationFeatures:
        """Extract comprehensive features for liquidation prediction"""
        # This would be implemented with real market data analysis
        # For now, using simplified feature extraction

        symbol = asset.get('symbol', 'UNKNOWN')
        price = asset.get('current_price', 0)
        volume = asset.get('daily_volume', 0)
        market_cap = asset.get('market_cap', 0)

        # Calculate technical indicators (simplified)
        price_volatility = asset.get('volatility_30d', 0.3)
        volume_volatility = 0.2  # Placeholder

        # Market sentiment and conditions
        market_sentiment = market_conditions.get('sentiment', 0.0) if market_conditions else 0.0
        volatility_index = market_conditions.get('volatility_index', 0.3) if market_conditions else 0.3

        return LiquidationFeatures(
            price_volatility=price_volatility,
            price_momentum=0.0,  # Would calculate from price history
            price_trend=0.0,     # Would calculate from price history
            relative_strength_index=0.5,  # Would calculate RSI
            bollinger_position=0.0,       # Would calculate Bollinger position
            volume_trend=0.0,             # Would calculate from volume history
            volume_volatility=volume_volatility,
            volume_price_divergence=0.0,  # Would calculate divergence
            liquidity_ratio=min(volume / max(market_cap, 1), 1.0),
            market_cap=market_cap,
            trading_pairs=asset.get('trading_pairs', 1),
            exchange_concentration=0.5,   # Would calculate from exchange data
            order_book_depth=0.5,         # Would calculate from order book
            market_correlation=asset.get('correlation_btc', 0.5),
            sector_correlation=0.5,       # Would calculate sector correlation
            systematic_risk_exposure=0.5, # Would calculate systematic risk
            market_sentiment=market_sentiment,
            volatility_index=volatility_index,
            funding_rates=0.0            # Would get from funding rate data
        )

    def _features_to_vector(self, features: LiquidationFeatures) -> List[float]:
        """Convert features object to vector for ML model"""
        return [
            features.price_volatility,
            features.price_momentum,
            features.volume_trend,
            features.market_correlation,
            features.liquidity_ratio,
            features.market_sentiment,
            features.volatility_index,
            features.relative_strength_index,
            features.bollinger_position
        ]

    def _probability_to_risk_level(self, probability: float) -> str:
        """Convert probability to risk level"""
        thresholds = self.liquidation_config['risk_thresholds']

        if probability <= thresholds['very_low']:
            return 'very_low'
        elif probability <= thresholds['low']:
            return 'low'
        elif probability <= thresholds['medium']:
            return 'medium'
        elif probability <= thresholds['high']:
            return 'high'
        else:
            return 'very_high'

    def _calculate_contributing_factors(self,
                                      features: LiquidationFeatures,
                                      model,
                                      feature_vector: np.ndarray) -> Dict[str, float]:
        """Calculate contributing factors to liquidation risk"""
        try:
            # Get feature importance from the model
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                feature_names = [
                    'price_volatility', 'price_momentum', 'volume_trend',
                    'market_correlation', 'liquidity_ratio', 'market_sentiment',
                    'volatility_index', 'relative_strength_index', 'bollinger_position'
                ]

                # Weight by actual feature values
                feature_values = feature_vector[0]
                weighted_contributions = importances * np.abs(feature_values)

                # Normalize to sum to 1
                total_contribution = np.sum(weighted_contributions)
                if total_contribution > 0:
                    normalized_contributions = weighted_contributions / total_contribution
                else:
                    normalized_contributions = np.ones(len(feature_names)) / len(feature_names)

                return {
                    name: round(contrib, 3)
                    for name, contrib in zip(feature_names, normalized_contributions)
                }
            else:
                # Fallback: equal weights
                feature_names = ['price_volatility', 'market_correlation', 'liquidity_ratio']
                return {name: 0.33 for name in feature_names}

        except Exception as e:
            self.logger.error(f"Error calculating contributing factors: {str(e)}")
            return {'unknown': 1.0}

    def _calculate_portfolio_liquidation_risk(self,
                                            asset_predictions: List[LiquidationPrediction],
                                            collateral_assets: List[Dict]) -> PortfolioLiquidationRisk:
        """Calculate portfolio-level liquidation risk"""
        if not asset_predictions:
            return PortfolioLiquidationRisk(
                overall_liquidation_probability=0.0,
                worst_case_scenario_probability=0.0,
                expected_liquidation_value=0.0,
                time_to_liquidation_estimate=None,
                cascade_risk_probability=0.0,
                stress_test_results={}
            )

        # Calculate overall probability (not simple average due to correlations)
        short_term_probs = [p.liquidation_probability for p in asset_predictions if p.prediction_horizon == 'short_term']
        medium_term_probs = [p.liquidation_probability for p in asset_predictions if p.prediction_horizon == 'medium_term']

        # Portfolio probability considering correlations (simplified)
        if short_term_probs:
            correlation_adjustment = 0.8  # Assume some correlation
            overall_prob = 1 - np.prod([1 - p * correlation_adjustment for p in short_term_probs])
        else:
            overall_prob = 0.0

        # Worst case scenario (highest individual asset risk)
        worst_case_prob = max([p.liquidation_probability for p in asset_predictions], default=0.0)

        # Expected liquidation value (weighted by probabilities)
        total_value = sum(asset.get('current_price', 0) * asset.get('amount', 0) for asset in collateral_assets)
        expected_liquidation_value = total_value * overall_prob

        # Time to liquidation estimate
        high_risk_predictions = [p for p in asset_predictions if p.liquidation_probability > 0.5]
        if high_risk_predictions:
            horizon_days = {
                'short_term': self.liquidation_config['prediction_horizons']['short_term'],
                'medium_term': self.liquidation_config['prediction_horizons']['medium_term'],
                'long_term': self.liquidation_config['prediction_horizons']['long_term']
            }
            estimated_days = min([horizon_days[p.prediction_horizon] for p in high_risk_predictions])
        else:
            estimated_days = None

        # Cascade risk (simplified)
        cascade_risk = min(overall_prob * 1.5, 1.0)  # Higher if overall risk is high

        # Stress test results
        stress_test_results = self._perform_stress_tests(asset_predictions)

        return PortfolioLiquidationRisk(
            overall_liquidation_probability=round(overall_prob, 3),
            worst_case_scenario_probability=round(worst_case_prob, 3),
            expected_liquidation_value=round(expected_liquidation_value, 2),
            time_to_liquidation_estimate=estimated_days,
            cascade_risk_probability=round(cascade_risk, 3),
            stress_test_results=stress_test_results
        )

    def _perform_stress_tests(self, predictions: List[LiquidationPrediction]) -> Dict[str, float]:
        """Perform stress testing scenarios"""
        stress_scenarios = {
            'market_crash_20': 0.0,
            'market_crash_40': 0.0,
            'liquidity_crisis': 0.0,
            'correlation_spike': 0.0
        }

        if not predictions:
            return stress_scenarios

        # Market crash scenarios (increase all probabilities)
        base_prob = np.mean([p.liquidation_probability for p in predictions])

        stress_scenarios['market_crash_20'] = min(base_prob * 1.5, 1.0)
        stress_scenarios['market_crash_40'] = min(base_prob * 2.5, 1.0)
        stress_scenarios['liquidity_crisis'] = min(base_prob * 2.0, 1.0)
        stress_scenarios['correlation_spike'] = min(base_prob * 1.8, 1.0)

        return {k: round(v, 3) for k, v in stress_scenarios.items()}

    def _get_model_performance_metrics(self) -> Dict[str, float]:
        """Get model performance metrics"""
        performance = {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT model_name, AVG(validation_auc), AVG(cross_val_score)
                FROM model_performance
                GROUP BY model_name
            """)

            for row in cursor.fetchall():
                model_name, avg_auc, avg_cv = row
                performance[f'{model_name}_auc'] = avg_auc if avg_auc else 0.7
                performance[f'{model_name}_cv_score'] = avg_cv if avg_cv else 0.7

        return performance

    def _calculate_feature_importance(self) -> Dict[str, float]:
        """Calculate overall feature importance across models"""
        feature_importance = defaultdict(float)
        model_count = 0

        for horizon, model in self.models.items():
            if hasattr(model, 'feature_importances_'):
                feature_names = [
                    'price_volatility', 'price_momentum', 'volume_trend',
                    'market_correlation', 'liquidity_ratio', 'market_sentiment',
                    'volatility_index', 'relative_strength_index', 'bollinger_position'
                ]

                for name, importance in zip(feature_names, model.feature_importances_):
                    feature_importance[name] += importance

                model_count += 1

        # Average across models
        if model_count > 0:
            feature_importance = {k: round(v / model_count, 3) for k, v in feature_importance.items()}

        return dict(feature_importance)

    def _generate_risk_mitigation_strategies(self,
                                           predictions: List[LiquidationPrediction],
                                           portfolio_risk: PortfolioLiquidationRisk) -> List[str]:
        """Generate risk mitigation strategies"""
        strategies = []

        # High-risk asset strategies
        high_risk_assets = [p for p in predictions if p.liquidation_probability > 0.5]
        if high_risk_assets:
            strategies.append(f"Consider reducing exposure to high-risk assets: {', '.join([p.asset_symbol for p in high_risk_assets])}")

        # Portfolio diversification
        if portfolio_risk.overall_liquidation_probability > 0.3:
            strategies.append("Increase portfolio diversification to reduce overall liquidation risk")

        # Liquidity management
        liquidity_risk_assets = [
            p for p in predictions
            if p.contributing_factors.get('liquidity_ratio', 0) > 0.3
        ]
        if liquidity_risk_assets:
            strategies.append("Monitor liquidity conditions for assets with high liquidity risk")

        # Volatility management
        volatile_assets = [
            p for p in predictions
            if p.contributing_factors.get('price_volatility', 0) > 0.3
        ]
        if volatile_assets:
            strategies.append("Consider hedging strategies for high-volatility assets")

        # Time-based strategies
        if portfolio_risk.time_to_liquidation_estimate and portfolio_risk.time_to_liquidation_estimate < 14:
            strategies.append("URGENT: Take immediate action to reduce liquidation risk within 2 weeks")

        return strategies

    def _identify_early_warning_indicators(self,
                                         predictions: List[LiquidationPrediction],
                                         portfolio_risk: PortfolioLiquidationRisk) -> List[str]:
        """Identify early warning indicators"""
        warnings = []

        # Probability thresholds
        if portfolio_risk.overall_liquidation_probability > 0.5:
            warnings.append("CRITICAL: High portfolio liquidation probability detected")

        # Individual asset warnings
        very_high_risk = [p for p in predictions if p.risk_level == 'very_high']
        if very_high_risk:
            warnings.append(f"HIGH RISK: Very high liquidation risk for {len(very_high_risk)} assets")

        # Cascade risk warning
        if portfolio_risk.cascade_risk_probability > 0.4:
            warnings.append("CASCADE RISK: High probability of cascading liquidations")

        # Time-sensitive warnings
        if portfolio_risk.time_to_liquidation_estimate and portfolio_risk.time_to_liquidation_estimate <= 7:
            warnings.append("IMMEDIATE ACTION REQUIRED: Liquidation risk within 7 days")

        # Model confidence warnings
        low_confidence_predictions = [p for p in predictions if p.model_confidence < 0.6]
        if len(low_confidence_predictions) > len(predictions) * 0.5:
            warnings.append("Model confidence is low for several predictions")

        return warnings

    def _calculate_prediction_confidence(self,
                                       predictions: List[LiquidationPrediction],
                                       model_performance: Dict[str, float]) -> float:
        """Calculate overall prediction confidence"""
        confidence_factors = []

        # Model performance factor
        avg_auc = np.mean([v for k, v in model_performance.items() if 'auc' in k])
        confidence_factors.append(avg_auc if avg_auc else 0.7)

        # Individual prediction confidence
        if predictions:
            avg_model_confidence = np.mean([p.model_confidence for p in predictions])
            confidence_factors.append(avg_model_confidence)

        # Data quality factor (based on feature completeness)
        data_quality = 0.8  # Simplified assumption
        confidence_factors.append(data_quality)

        return round(np.mean(confidence_factors), 3) if confidence_factors else 0.5

    def _get_model_confidence(self, horizon: str) -> float:
        """Get confidence level for specific model"""
        # Would be based on validation performance
        return 0.75  # Placeholder

    def _store_model_performance(self, model_name: str, validation_auc: float, cross_val_score: float, training_samples: int):
        """Store model performance metrics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO model_performance
                (model_name, training_date, validation_auc, cross_val_score, feature_count, training_samples)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                model_name,
                datetime.now(),
                validation_auc,
                cross_val_score,
                9,  # Number of features
                training_samples
            ))
            conn.commit()

    async def _store_predictions(self, analysis: LiquidationPredictionAnalysis):
        """Store prediction results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for prediction in analysis.asset_predictions:
                    features_dict = {
                        'contributing_factors': prediction.contributing_factors,
                        'confidence_interval': prediction.confidence_interval,
                        'model_confidence': prediction.model_confidence
                    }

                    cursor.execute("""
                        INSERT INTO liquidation_predictions
                        (address, asset_symbol, prediction_date, horizon, probability, confidence, features)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        analysis.address,
                        prediction.asset_symbol,
                        analysis.analysis_timestamp,
                        prediction.prediction_horizon,
                        prediction.liquidation_probability,
                        prediction.model_confidence,
                        json.dumps(features_dict)
                    ))

                conn.commit()
                self.logger.info("Predictions stored successfully")

        except Exception as e:
            self.logger.error(f"Error storing predictions: {str(e)}")

    def save_models(self):
        """Save trained models to disk"""
        model_dir = Path(__file__).parent.parent / "models"
        model_dir.mkdir(exist_ok=True)

        for horizon in self.models:
            try:
                model_path = model_dir / f"liquidation_model_{horizon}.joblib"
                scaler_path = model_dir / f"scaler_{horizon}.joblib"

                joblib.dump(self.models[horizon], model_path)
                joblib.dump(self.scalers[horizon], scaler_path)

                self.logger.info(f"Saved model for {horizon}")

            except Exception as e:
                self.logger.error(f"Error saving model for {horizon}: {str(e)}")