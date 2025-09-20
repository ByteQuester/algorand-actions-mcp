"""
Algorand Validation Utilities

Validation functions for Algorand addresses, transactions, and data integrity
in the loan decision process.
"""

import re
import base64
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class AlgorandValidator:
    """
    Comprehensive validation utilities for Algorand ecosystem data
    used in loan decision processes.
    """

    # Algorand address constants
    ALGORAND_ADDRESS_LENGTH = 58
    ALGORAND_CHECKSUM_LENGTH = 4

    # Asset ID constraints
    MAX_ASSET_ID = 2**64 - 1
    ALGO_ASSET_ID = 0

    # Transaction constraints
    MIN_TRANSACTION_FEE = 1000  # microAlgos
    MAX_NOTE_LENGTH = 1024

    def __init__(self):
        self.known_malicious_addresses = self._load_malicious_addresses()
        self.verified_assets = self._load_verified_assets()
        self.trusted_applications = self._load_trusted_applications()

    def validate_algorand_address(self, address: str) -> ValidationResult:
        """
        Validate Algorand wallet address format and checksum.

        Args:
            address: Algorand address to validate

        Returns:
            ValidationResult with validation status
        """
        try:
            if not address:
                return ValidationResult(
                    is_valid=False,
                    error_message="Address cannot be empty"
                )

            # Length check
            if len(address) != self.ALGORAND_ADDRESS_LENGTH:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Address must be {self.ALGORAND_ADDRESS_LENGTH} characters, got {len(address)}"
                )

            # Character set check (base32)
            if not re.match(r'^[A-Z2-7]+$', address):
                return ValidationResult(
                    is_valid=False,
                    error_message="Address contains invalid characters (must be base32)"
                )

            # Checksum validation
            checksum_valid = self._validate_address_checksum(address)
            if not checksum_valid:
                return ValidationResult(
                    is_valid=False,
                    error_message="Invalid address checksum"
                )

            # Malicious address check
            warnings = []
            if address in self.known_malicious_addresses:
                warnings.append("Address is on malicious address list")

            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                metadata={'address_type': 'standard'}
            )

        except Exception as e:
            logger.error(f"Address validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )

    def validate_asset_id(self, asset_id: Union[int, str]) -> ValidationResult:
        """
        Validate Algorand asset ID.

        Args:
            asset_id: Asset ID to validate

        Returns:
            ValidationResult with validation status
        """
        try:
            # Convert to integer if string
            if isinstance(asset_id, str):
                try:
                    asset_id = int(asset_id)
                except ValueError:
                    return ValidationResult(
                        is_valid=False,
                        error_message="Asset ID must be a valid integer"
                    )

            # Range check
            if asset_id < 0 or asset_id > self.MAX_ASSET_ID:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Asset ID must be between 0 and {self.MAX_ASSET_ID}"
                )

            # Determine asset type
            asset_type = "ALGO" if asset_id == 0 else "ASA"
            is_verified = asset_id in self.verified_assets

            warnings = []
            if not is_verified and asset_id != 0:
                warnings.append("Asset is not verified")

            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                metadata={
                    'asset_type': asset_type,
                    'is_verified': is_verified
                }
            )

        except Exception as e:
            logger.error(f"Asset ID validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )

    def validate_transaction_data(self, transaction_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate transaction data structure and content.

        Args:
            transaction_data: Transaction data to validate

        Returns:
            ValidationResult with validation status
        """
        try:
            required_fields = ['id', 'sender', 'fee', 'type']
            missing_fields = [field for field in required_fields if field not in transaction_data]

            if missing_fields:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Missing required fields: {', '.join(missing_fields)}"
                )

            warnings = []

            # Validate sender address
            sender_validation = self.validate_algorand_address(transaction_data['sender'])
            if not sender_validation.is_valid:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Invalid sender address: {sender_validation.error_message}"
                )
            warnings.extend(sender_validation.warnings)

            # Validate receiver if present
            if 'receiver' in transaction_data and transaction_data['receiver']:
                receiver_validation = self.validate_algorand_address(transaction_data['receiver'])
                if not receiver_validation.is_valid:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Invalid receiver address: {receiver_validation.error_message}"
                    )
                warnings.extend(receiver_validation.warnings)

            # Validate fee
            fee = transaction_data.get('fee', 0)
            if fee < self.MIN_TRANSACTION_FEE:
                warnings.append(f"Transaction fee {fee} is below minimum {self.MIN_TRANSACTION_FEE}")

            # Validate amount
            amount = transaction_data.get('amount', 0)
            if amount < 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="Transaction amount cannot be negative"
                )

            # Validate asset transfer
            if 'asset_id' in transaction_data:
                asset_validation = self.validate_asset_id(transaction_data['asset_id'])
                if not asset_validation.is_valid:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Invalid asset ID: {asset_validation.error_message}"
                    )
                warnings.extend(asset_validation.warnings)

            # Validate application call
            if 'app_id' in transaction_data and transaction_data['app_id']:
                app_validation = self.validate_application_id(transaction_data['app_id'])
                if not app_validation.is_valid:
                    warnings.append(f"Application validation: {app_validation.error_message}")

            # Validate note field
            if 'note' in transaction_data and transaction_data['note']:
                note_validation = self.validate_transaction_note(transaction_data['note'])
                if not note_validation.is_valid:
                    warnings.append(f"Note validation: {note_validation.error_message}")

            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                metadata={'transaction_type': transaction_data.get('type')}
            )

        except Exception as e:
            logger.error(f"Transaction validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )

    def validate_loan_request_data(self, loan_request: Dict[str, Any]) -> ValidationResult:
        """
        Validate loan request data for completeness and correctness.

        Args:
            loan_request: Loan request data to validate

        Returns:
            ValidationResult with validation status
        """
        try:
            required_fields = [
                'borrower_address', 'requested_amount', 'duration_days',
                'loan_purpose', 'proposed_collateral_amount'
            ]

            missing_fields = [field for field in required_fields if field not in loan_request]
            if missing_fields:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Missing required fields: {', '.join(missing_fields)}"
                )

            warnings = []

            # Validate borrower address
            address_validation = self.validate_algorand_address(loan_request['borrower_address'])
            if not address_validation.is_valid:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Invalid borrower address: {address_validation.error_message}"
                )
            warnings.extend(address_validation.warnings)

            # Validate amounts
            requested_amount = loan_request.get('requested_amount', 0)
            if requested_amount <= 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="Requested amount must be positive"
                )

            if requested_amount > 10_000_000:  # 10M limit
                warnings.append("Requested amount exceeds typical limits")

            collateral_amount = loan_request.get('proposed_collateral_amount', 0)
            if collateral_amount < 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="Collateral amount cannot be negative"
                )

            # Validate duration
            duration = loan_request.get('duration_days', 0)
            if duration <= 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="Loan duration must be positive"
                )

            if duration > 1095:  # 3 years max
                warnings.append("Loan duration exceeds typical maximum (3 years)")

            # Validate collateral assets
            if 'proposed_collateral_assets' in loan_request:
                for asset_id in loan_request['proposed_collateral_assets']:
                    asset_validation = self.validate_asset_id(asset_id)
                    if not asset_validation.is_valid:
                        warnings.append(f"Invalid collateral asset {asset_id}: {asset_validation.error_message}")

            # Validate loan purpose
            purpose = loan_request.get('loan_purpose', '').strip()
            if not purpose:
                warnings.append("Loan purpose not specified")
            elif len(purpose) > 500:
                warnings.append("Loan purpose description is very long")

            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                metadata={
                    'amount_range': self._categorize_loan_amount(requested_amount),
                    'duration_range': self._categorize_loan_duration(duration)
                }
            )

        except Exception as e:
            logger.error(f"Loan request validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )

    def validate_borrower_profile_data(self, profile_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate borrower profile data for consistency and completeness.

        Args:
            profile_data: Borrower profile data to validate

        Returns:
            ValidationResult with validation status
        """
        try:
            required_fields = [
                'wallet_address', 'wallet_age_days', 'total_transaction_count',
                'asset_count', 'dapp_count'
            ]

            missing_fields = [field for field in required_fields if field not in profile_data]
            if missing_fields:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Missing required fields: {', '.join(missing_fields)}"
                )

            warnings = []

            # Validate wallet address
            address_validation = self.validate_algorand_address(profile_data['wallet_address'])
            if not address_validation.is_valid:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Invalid wallet address: {address_validation.error_message}"
                )
            warnings.extend(address_validation.warnings)

            # Validate numeric fields
            numeric_fields = [
                'wallet_age_days', 'total_transaction_count', 'total_volume_algo',
                'asset_count', 'nft_count', 'smart_contract_interactions', 'dapp_count'
            ]

            for field in numeric_fields:
                if field in profile_data:
                    value = profile_data[field]
                    if not isinstance(value, (int, float)) or value < 0:
                        return ValidationResult(
                            is_valid=False,
                            error_message=f"{field} must be a non-negative number"
                        )

            # Validate reputation score
            reputation_score = profile_data.get('reputation_score', 0)
            if not (0 <= reputation_score <= 100):
                warnings.append("Reputation score should be between 0 and 100")

            # Consistency checks
            wallet_age = profile_data.get('wallet_age_days', 0)
            tx_count = profile_data.get('total_transaction_count', 0)

            # Very new wallets shouldn't have many transactions
            if wallet_age < 7 and tx_count > 100:
                warnings.append("High transaction count for very new wallet")

            # Very old wallets with no activity
            if wallet_age > 365 and tx_count < 10:
                warnings.append("Very low activity for mature wallet")

            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                metadata={
                    'profile_completeness': self._calculate_profile_completeness(profile_data),
                    'activity_level': self._categorize_activity_level(profile_data)
                }
            )

        except Exception as e:
            logger.error(f"Profile validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )

    def validate_application_id(self, app_id: Union[int, str]) -> ValidationResult:
        """
        Validate Algorand application ID.

        Args:
            app_id: Application ID to validate

        Returns:
            ValidationResult with validation status
        """
        try:
            if isinstance(app_id, str):
                try:
                    app_id = int(app_id)
                except ValueError:
                    return ValidationResult(
                        is_valid=False,
                        error_message="Application ID must be a valid integer"
                    )

            if app_id <= 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="Application ID must be positive"
                )

            is_trusted = app_id in self.trusted_applications
            warnings = []
            if not is_trusted:
                warnings.append("Application is not in trusted list")

            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                metadata={'is_trusted': is_trusted}
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )

    def validate_transaction_note(self, note: str) -> ValidationResult:
        """
        Validate transaction note field.

        Args:
            note: Transaction note to validate

        Returns:
            ValidationResult with validation status
        """
        if not note:
            return ValidationResult(is_valid=True)

        try:
            # Length check
            if len(note) > self.MAX_NOTE_LENGTH:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Note exceeds maximum length of {self.MAX_NOTE_LENGTH} bytes"
                )

            # Try to decode if it looks like base64
            warnings = []
            if self._is_base64(note):
                try:
                    decoded = base64.b64decode(note)
                    # Check for suspicious patterns
                    if b'http' in decoded.lower():
                        warnings.append("Note contains URL - potential phishing risk")
                except:
                    warnings.append("Note appears to be malformed base64")

            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                metadata={'note_length': len(note)}
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )

    def validate_risk_assessment_data(self, risk_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate risk assessment data structure and ranges.

        Args:
            risk_data: Risk assessment data to validate

        Returns:
            ValidationResult with validation status
        """
        try:
            required_fields = ['overall_risk_score', 'risk_level']
            missing_fields = [field for field in required_fields if field not in risk_data]

            if missing_fields:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Missing required fields: {', '.join(missing_fields)}"
                )

            warnings = []

            # Validate risk score range
            risk_score = risk_data.get('overall_risk_score')
            if not isinstance(risk_score, (int, float)) or not (0 <= risk_score <= 100):
                return ValidationResult(
                    is_valid=False,
                    error_message="Overall risk score must be between 0 and 100"
                )

            # Validate component scores
            component_fields = [
                'wallet_age_risk', 'transaction_volume_risk', 'asset_diversity_risk',
                'governance_participation_risk', 'defi_behavior_risk', 'cross_protocol_risk'
            ]

            for field in component_fields:
                if field in risk_data:
                    value = risk_data[field]
                    if not isinstance(value, (int, float)) or not (0 <= value <= 100):
                        warnings.append(f"{field} should be between 0 and 100")

            # Validate risk level
            valid_risk_levels = ['very_low', 'low', 'medium', 'high', 'very_high']
            risk_level = risk_data.get('risk_level')
            if risk_level not in valid_risk_levels:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Risk level must be one of: {', '.join(valid_risk_levels)}"
                )

            # Consistency check between score and level
            score_level_consistent = self._check_score_level_consistency(risk_score, risk_level)
            if not score_level_consistent:
                warnings.append("Risk score and risk level appear inconsistent")

            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                metadata={'score_level_consistent': score_level_consistent}
            )

        except Exception as e:
            logger.error(f"Risk assessment validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )

    def validate_batch_data(self, data_list: List[Dict[str, Any]], validation_type: str) -> Dict[str, Any]:
        """
        Validate a batch of data items.

        Args:
            data_list: List of data items to validate
            validation_type: Type of validation ('address', 'transaction', 'loan_request', etc.)

        Returns:
            Dictionary with batch validation results
        """
        validation_methods = {
            'address': lambda x: self.validate_algorand_address(x.get('address', '')),
            'transaction': self.validate_transaction_data,
            'loan_request': self.validate_loan_request_data,
            'borrower_profile': self.validate_borrower_profile_data,
            'risk_assessment': self.validate_risk_assessment_data
        }

        if validation_type not in validation_methods:
            raise ValueError(f"Unknown validation type: {validation_type}")

        validator = validation_methods[validation_type]
        results = {
            'total_items': len(data_list),
            'valid_items': 0,
            'invalid_items': 0,
            'items_with_warnings': 0,
            'validation_details': [],
            'summary_warnings': [],
            'summary_errors': []
        }

        for i, item in enumerate(data_list):
            try:
                validation_result = validator(item)

                results['validation_details'].append({
                    'index': i,
                    'is_valid': validation_result.is_valid,
                    'error_message': validation_result.error_message,
                    'warnings': validation_result.warnings,
                    'metadata': validation_result.metadata
                })

                if validation_result.is_valid:
                    results['valid_items'] += 1
                    if validation_result.warnings:
                        results['items_with_warnings'] += 1
                else:
                    results['invalid_items'] += 1
                    results['summary_errors'].append(f"Item {i}: {validation_result.error_message}")

            except Exception as e:
                results['invalid_items'] += 1
                results['summary_errors'].append(f"Item {i}: Validation exception - {str(e)}")

        # Generate summary warnings
        if results['invalid_items'] > 0:
            results['summary_warnings'].append(f"{results['invalid_items']} items failed validation")

        if results['items_with_warnings'] > 0:
            results['summary_warnings'].append(f"{results['items_with_warnings']} items have warnings")

        return results

    def _validate_address_checksum(self, address: str) -> bool:
        """Validate Algorand address checksum"""
        try:
            # Decode the address
            decoded = base64.b32decode(address + '=' * (-len(address) % 8))

            # Split into public key and checksum
            public_key = decoded[:-self.ALGORAND_CHECKSUM_LENGTH]
            checksum = decoded[-self.ALGORAND_CHECKSUM_LENGTH:]

            # Calculate expected checksum
            expected_checksum = hashlib.sha512(hashlib.sha256(public_key).digest()).digest()[-self.ALGORAND_CHECKSUM_LENGTH:]

            return checksum == expected_checksum
        except:
            return False

    def _is_base64(self, s: str) -> bool:
        """Check if string looks like base64"""
        try:
            if len(s) % 4 != 0:
                return False
            base64.b64decode(s)
            return True
        except:
            return False

    def _categorize_loan_amount(self, amount: float) -> str:
        """Categorize loan amount"""
        if amount < 1000:
            return "micro"
        elif amount < 10000:
            return "small"
        elif amount < 100000:
            return "medium"
        elif amount < 1000000:
            return "large"
        else:
            return "very_large"

    def _categorize_loan_duration(self, days: int) -> str:
        """Categorize loan duration"""
        if days < 30:
            return "short_term"
        elif days < 180:
            return "medium_term"
        elif days < 365:
            return "long_term"
        else:
            return "very_long_term"

    def _calculate_profile_completeness(self, profile_data: Dict[str, Any]) -> float:
        """Calculate profile data completeness score"""
        total_fields = [
            'wallet_address', 'wallet_age_days', 'total_transaction_count',
            'total_volume_algo', 'asset_count', 'nft_count', 'smart_contract_interactions',
            'dapp_count', 'governance_participation', 'validator_participation',
            'reputation_score', 'ecosystem_tenure_months'
        ]

        present_fields = sum(1 for field in total_fields if field in profile_data and profile_data[field] is not None)
        return present_fields / len(total_fields)

    def _categorize_activity_level(self, profile_data: Dict[str, Any]) -> str:
        """Categorize borrower activity level"""
        tx_count = profile_data.get('total_transaction_count', 0)
        dapp_count = profile_data.get('dapp_count', 0)

        if tx_count > 1000 and dapp_count > 5:
            return "very_active"
        elif tx_count > 100 and dapp_count > 2:
            return "active"
        elif tx_count > 10:
            return "moderate"
        else:
            return "low"

    def _check_score_level_consistency(self, score: float, level: str) -> bool:
        """Check if risk score and level are consistent"""
        level_ranges = {
            'very_low': (0, 20),
            'low': (20, 40),
            'medium': (40, 60),
            'high': (60, 80),
            'very_high': (80, 100)
        }

        if level not in level_ranges:
            return False

        min_score, max_score = level_ranges[level]
        return min_score <= score <= max_score

    def _load_malicious_addresses(self) -> set:
        """Load known malicious addresses"""
        # In practice, this would load from a database or external service
        return {
            # Example malicious addresses (mock data)
            "MALICIOUSADDRESS1EXAMPLEONLY234567890ABCDEFGHIJKLMNOP",
            "SCAMADDRESS2EXAMPLEONLY3456789ABCDEFGHIJKLMNOPQRSTUVW"
        }

    def _load_verified_assets(self) -> set:
        """Load verified asset IDs"""
        # In practice, this would load from Algorand ecosystem databases
        return {
            0,          # ALGO
            31566704,   # USDC
            386192725,  # goBTC
            465865291,  # USDT
            444108880,  # Tinyman Pool Token
        }

    def _load_trusted_applications(self) -> set:
        """Load trusted application IDs"""
        # In practice, this would load from curated lists
        return {
            350338509,  # Tinyman AMM
            465814065,  # Algofi
            552635992,  # Folks Finance
            624956175,  # Pact DEX
        }