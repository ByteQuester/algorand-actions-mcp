"""
Smart Contract Security Analysis Engine
Analyzes ASA smart contract security, audit status, and technical parameters.
"""

import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib

from algosdk.v2client import algod, indexer
from algosdk import encoding, transaction


@dataclass
class ContractAudit:
    """Smart contract audit information"""
    auditor: str
    audit_date: datetime
    score: float
    severity_findings: Dict[str, int]  # critical, high, medium, low
    report_url: str
    is_current: bool  # Within valid timeframe


@dataclass
class TechnicalParameters:
    """ASA technical parameter analysis"""
    total_supply: int
    decimals: int
    default_frozen: bool
    freeze_enabled: bool
    clawback_enabled: bool
    manager_address: Optional[str]
    reserve_address: Optional[str]
    freeze_address: Optional[str]
    clawback_address: Optional[str]
    url: Optional[str]
    metadata_hash: Optional[str]


@dataclass
class CreatorAnalysis:
    """Asset creator reputation analysis"""
    creator_address: str
    is_verified: bool
    reputation_score: float
    previous_assets: List[int]
    governance_participation: bool
    community_standing: str
    kyc_status: bool
    social_presence: Dict[str, str]


@dataclass
class SecurityFlags:
    """Security warning flags"""
    centralized_control: bool
    unlimited_minting: bool
    freeze_risk: bool
    clawback_risk: bool
    unverified_creator: bool
    recent_creation: bool
    suspicious_parameters: bool
    missing_metadata: bool


@dataclass
class SecurityMetrics:
    """Comprehensive security analysis"""
    asset_id: int
    asset_name: str

    # Technical analysis
    technical_params: TechnicalParameters
    security_flags: SecurityFlags

    # Audit information
    audits: List[ContractAudit]
    latest_audit_score: float
    audit_coverage: float

    # Creator analysis
    creator_analysis: CreatorAnalysis

    # Smart contract analysis
    contract_complexity: float
    code_quality_score: float
    upgrade_mechanism: Optional[str]

    # Security scores
    technical_security_score: float
    audit_security_score: float
    creator_security_score: float
    overall_security_score: float

    # Risk assessment
    security_risk_level: str
    recommendations: List[str]


class SmartContractSecurityAnalyzer:
    """Analyzes ASA smart contract security characteristics"""

    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize clients
        self.indexer_client = indexer.IndexerClient(
            indexer_token="",
            indexer_address=config['algorand_config']['indexer']['url']
        )

        self.algod_client = algod.AlgodClient(
            algod_token="",
            algod_address=config['algorand_config']['node']['url']
        )

        # Security configuration
        self.security_config = config['security_analysis']

        # Known audit providers
        self.audit_providers = {
            'certik': {'reputation': 0.95, 'weight': 1.0},
            'halborn': {'reputation': 0.90, 'weight': 0.9},
            'trail_of_bits': {'reputation': 0.92, 'weight': 0.95},
            'consensys': {'reputation': 0.88, 'weight': 0.85},
            'openzeppelin': {'reputation': 0.90, 'weight': 0.9}
        }

        # Verified creators
        self.verified_creators = set(self.security_config['creator_verification']['verified_creators'])

    async def analyze_contract_security(self, asset_id: int) -> SecurityMetrics:
        """Perform comprehensive smart contract security analysis"""
        try:
            self.logger.info(f"Analyzing contract security for ASA {asset_id}")

            # Get asset information
            asset_info = await self._get_asset_info(asset_id)
            if not asset_info:
                raise ValueError(f"Could not retrieve asset info for {asset_id}")

            asset_name = asset_info.get('params', {}).get('name', f'ASA-{asset_id}')

            # Run parallel analysis
            results = await asyncio.gather(
                self._analyze_technical_parameters(asset_info),
                self._analyze_creator_reputation(asset_info),
                self._analyze_audit_status(asset_id),
                self._analyze_contract_complexity(asset_id),
                return_exceptions=True
            )

            # Extract results
            technical_params = results[0] if not isinstance(results[0], Exception) else self._default_technical_params()
            creator_analysis = results[1] if not isinstance(results[1], Exception) else self._default_creator_analysis(asset_info)
            audits = results[2] if not isinstance(results[2], Exception) else []
            contract_complexity = results[3] if not isinstance(results[3], Exception) else 0.5

            # Generate security flags
            security_flags = self._generate_security_flags(technical_params, creator_analysis, asset_info)

            # Calculate security scores
            technical_security_score = self._calculate_technical_security_score(technical_params, security_flags)
            audit_security_score = self._calculate_audit_security_score(audits)
            creator_security_score = creator_analysis.reputation_score

            # Overall security score
            overall_score = self._calculate_overall_security_score(
                technical_security_score, audit_security_score, creator_security_score
            )

            # Determine risk level
            security_risk_level = self._determine_security_risk_level(overall_score)

            # Generate recommendations
            recommendations = self._generate_security_recommendations(security_flags, audits, creator_analysis)

            # Additional metrics
            latest_audit_score = max([audit.score for audit in audits], default=0.0)
            audit_coverage = self._calculate_audit_coverage(audits)
            code_quality_score = self._estimate_code_quality(technical_params, contract_complexity)

            return SecurityMetrics(
                asset_id=asset_id,
                asset_name=asset_name,
                technical_params=technical_params,
                security_flags=security_flags,
                audits=audits,
                latest_audit_score=latest_audit_score,
                audit_coverage=audit_coverage,
                creator_analysis=creator_analysis,
                contract_complexity=contract_complexity,
                code_quality_score=code_quality_score,
                upgrade_mechanism=self._detect_upgrade_mechanism(technical_params),
                technical_security_score=technical_security_score,
                audit_security_score=audit_security_score,
                creator_security_score=creator_security_score,
                overall_security_score=overall_score,
                security_risk_level=security_risk_level,
                recommendations=recommendations
            )

        except Exception as e:
            self.logger.error(f"Error analyzing contract security for ASA {asset_id}: {e}")
            raise

    async def _analyze_technical_parameters(self, asset_info: Dict) -> TechnicalParameters:
        """Analyze ASA technical parameters"""
        try:
            params = asset_info.get('params', {})

            return TechnicalParameters(
                total_supply=params.get('total', 0),
                decimals=params.get('decimals', 0),
                default_frozen=params.get('default-frozen', False),
                freeze_enabled=bool(params.get('freeze')),
                clawback_enabled=bool(params.get('clawback')),
                manager_address=params.get('manager'),
                reserve_address=params.get('reserve'),
                freeze_address=params.get('freeze'),
                clawback_address=params.get('clawback'),
                url=params.get('url'),
                metadata_hash=params.get('metadata-hash')
            )

        except Exception as e:
            self.logger.error(f"Error analyzing technical parameters: {e}")
            return self._default_technical_params()

    async def _analyze_creator_reputation(self, asset_info: Dict) -> CreatorAnalysis:
        """Analyze asset creator reputation"""
        try:
            params = asset_info.get('params', {})
            creator_address = params.get('creator', '')

            # Check if creator is verified
            is_verified = creator_address in self.verified_creators

            # Analyze creator's previous assets
            previous_assets = await self._get_creator_assets(creator_address)

            # Check governance participation
            governance_participation = await self._check_governance_participation(creator_address)

            # Calculate reputation score
            reputation_score = self._calculate_creator_reputation_score(
                is_verified, len(previous_assets), governance_participation
            )

            # Determine community standing
            community_standing = self._assess_community_standing(reputation_score, is_verified)

            return CreatorAnalysis(
                creator_address=creator_address,
                is_verified=is_verified,
                reputation_score=reputation_score,
                previous_assets=previous_assets,
                governance_participation=governance_participation,
                community_standing=community_standing,
                kyc_status=is_verified,  # Simplified - verified implies KYC
                social_presence={}  # Would be populated from external sources
            )

        except Exception as e:
            self.logger.error(f"Error analyzing creator reputation: {e}")
            return self._default_creator_analysis(asset_info)

    async def _analyze_audit_status(self, asset_id: int) -> List[ContractAudit]:
        """Analyze audit status and history"""
        try:
            audits = []

            # Check known audit databases (would integrate with real audit APIs)
            audit_sources = ['certik', 'halborn', 'trail_of_bits']

            for source in audit_sources:
                audit_info = await self._check_audit_source(asset_id, source)
                if audit_info:
                    audits.append(audit_info)

            return audits

        except Exception as e:
            self.logger.error(f"Error analyzing audit status: {e}")
            return []

    async def _analyze_contract_complexity(self, asset_id: int) -> float:
        """Analyze smart contract complexity"""
        try:
            # For ASAs, complexity is generally low as they use standard Algorand asset functionality
            # This would analyze any associated smart contracts

            # Get application info if the ASA has associated smart contracts
            complexity_score = 0.1  # Low complexity for standard ASA

            # Check for associated applications
            app_info = await self._get_associated_applications(asset_id)
            if app_info:
                complexity_score += len(app_info) * 0.1

            return min(1.0, complexity_score)

        except Exception as e:
            self.logger.error(f"Error analyzing contract complexity: {e}")
            return 0.5

    async def _get_creator_assets(self, creator_address: str) -> List[int]:
        """Get assets created by this address"""
        try:
            response = self.indexer_client.search_assets(creator=creator_address)
            assets = response.get('assets', [])
            return [asset['index'] for asset in assets]

        except Exception as e:
            self.logger.error(f"Error getting creator assets: {e}")
            return []

    async def _check_governance_participation(self, address: str) -> bool:
        """Check if address participates in governance"""
        try:
            # This would check governance participation
            # For now, return a placeholder based on account activity
            account_info = self.algod_client.account_info(address)
            balance = account_info.get('amount', 0) / 1e6

            # Simple heuristic: accounts with significant ALGO balance likely participate
            return balance >= 1000  # 1000+ ALGO suggests possible governance participation

        except Exception as e:
            self.logger.error(f"Error checking governance participation: {e}")
            return False

    async def _check_audit_source(self, asset_id: int, source: str) -> Optional[ContractAudit]:
        """Check specific audit source for asset audit"""
        try:
            # This would integrate with real audit provider APIs
            # For now, return placeholder data for demonstration

            if source == 'certik' and asset_id in [31566704, 312769]:  # USDC, USDt
                return ContractAudit(
                    auditor='certik',
                    audit_date=datetime.utcnow() - timedelta(days=30),
                    score=0.95,
                    severity_findings={'critical': 0, 'high': 0, 'medium': 1, 'low': 2},
                    report_url=f'https://certik.io/audit/{asset_id}',
                    is_current=True
                )

            return None

        except Exception as e:
            self.logger.error(f"Error checking {source} audit: {e}")
            return None

    async def _get_associated_applications(self, asset_id: int) -> List[Dict]:
        """Get smart contracts associated with the ASA"""
        try:
            # This would find applications that reference the ASA
            # For now, return empty list
            return []

        except Exception as e:
            self.logger.error(f"Error getting associated applications: {e}")
            return []

    def _generate_security_flags(
        self, technical_params: TechnicalParameters,
        creator_analysis: CreatorAnalysis,
        asset_info: Dict
    ) -> SecurityFlags:
        """Generate security warning flags"""
        # Check creation date
        creation_round = asset_info.get('created-at-round', 0)
        current_round = 0  # Would get current round from algod
        recent_creation = (current_round - creation_round) < 100000  # Less than ~1 month

        return SecurityFlags(
            centralized_control=bool(technical_params.manager_address),
            unlimited_minting=technical_params.total_supply == 0,  # Total supply of 0 means unlimited
            freeze_risk=technical_params.freeze_enabled,
            clawback_risk=technical_params.clawback_enabled,
            unverified_creator=not creator_analysis.is_verified,
            recent_creation=recent_creation,
            suspicious_parameters=self._check_suspicious_parameters(technical_params),
            missing_metadata=not technical_params.url and not technical_params.metadata_hash
        )

    def _check_suspicious_parameters(self, params: TechnicalParameters) -> bool:
        """Check for suspicious parameter combinations"""
        # Check technical parameter requirements
        checks = self.security_config['technical_checks']

        suspicious = False

        # Check against security requirements
        if params.freeze_enabled and not checks['freeze_enabled']:
            suspicious = True

        if params.clawback_enabled and not checks['clawback_enabled']:
            suspicious = True

        if params.default_frozen and not checks['default_frozen']:
            suspicious = True

        # Check name/unit name lengths
        if params.asset_name and len(params.asset_name) > checks['asset_name_length']:
            suspicious = True

        return suspicious

    def _calculate_technical_security_score(
        self, params: TechnicalParameters, flags: SecurityFlags
    ) -> float:
        """Calculate technical security score"""
        score = 1.0

        # Penalties for risky parameters
        if flags.freeze_risk:
            score -= 0.2
        if flags.clawback_risk:
            score -= 0.3
        if flags.unlimited_minting:
            score -= 0.25
        if flags.centralized_control:
            score -= 0.15
        if flags.suspicious_parameters:
            score -= 0.1

        return max(0.0, score)

    def _calculate_audit_security_score(self, audits: List[ContractAudit]) -> float:
        """Calculate audit-based security score"""
        if not audits:
            return 0.0

        # Find current audits (within timeframe)
        current_audits = [audit for audit in audits if audit.is_current]

        if not current_audits:
            return 0.1  # Outdated audits get minimal credit

        # Weight audits by provider reputation
        weighted_score = 0.0
        total_weight = 0.0

        for audit in current_audits:
            provider_info = self.audit_providers.get(audit.auditor, {'reputation': 0.5, 'weight': 0.5})
            weight = provider_info['weight']
            weighted_score += audit.score * weight
            total_weight += weight

        return weighted_score / max(total_weight, 1.0) if total_weight > 0 else 0.0

    def _calculate_creator_reputation_score(
        self, is_verified: bool, asset_count: int, governance_participation: bool
    ) -> float:
        """Calculate creator reputation score"""
        score = 0.0

        # Base score for verification
        if is_verified:
            score += 0.5
        else:
            score += 0.1

        # Score for track record
        if asset_count >= 5:
            score += 0.3
        elif asset_count >= 2:
            score += 0.2
        elif asset_count >= 1:
            score += 0.1

        # Score for governance participation
        if governance_participation:
            score += 0.2

        return min(1.0, score)

    def _calculate_overall_security_score(
        self, technical_score: float, audit_score: float, creator_score: float
    ) -> float:
        """Calculate overall security score"""
        weights = self.config['risk_assessment']['security_weights']

        return (
            technical_score * weights['technical_parameters'] +
            audit_score * weights['smart_contract_audit'] +
            creator_score * weights['creator_reputation']
        )

    def _determine_security_risk_level(self, score: float) -> str:
        """Determine security risk level"""
        if score >= 0.9:
            return "very_low"
        elif score >= 0.8:
            return "low"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "high"
        else:
            return "very_high"

    def _generate_security_recommendations(
        self, flags: SecurityFlags, audits: List[ContractAudit], creator: CreatorAnalysis
    ) -> List[str]:
        """Generate security improvement recommendations"""
        recommendations = []

        if flags.freeze_risk:
            recommendations.append("Asset has freeze capability - verify legitimate use case")

        if flags.clawback_risk:
            recommendations.append("Asset has clawback capability - high centralization risk")

        if flags.unlimited_minting:
            recommendations.append("Unlimited minting enabled - monitor for supply inflation")

        if flags.unverified_creator:
            recommendations.append("Creator not verified - perform additional due diligence")

        if not audits:
            recommendations.append("No security audits found - recommend independent security review")

        if flags.recent_creation:
            recommendations.append("Recently created asset - allow time to establish track record")

        if flags.missing_metadata:
            recommendations.append("Missing metadata - verify asset authenticity through other means")

        if not recommendations:
            recommendations.append("Security analysis shows acceptable risk profile")

        return recommendations

    def _calculate_audit_coverage(self, audits: List[ContractAudit]) -> float:
        """Calculate audit coverage percentage"""
        if not audits:
            return 0.0

        # Check coverage of different audit aspects
        coverage_areas = {
            'smart_contract': False,
            'economic_model': False,
            'governance': False,
            'operational': False
        }

        # This would analyze audit reports to determine coverage
        # For now, assume basic coverage if any audits exist
        if audits:
            coverage_areas['smart_contract'] = True

        covered = sum(coverage_areas.values())
        total = len(coverage_areas)

        return covered / total

    def _estimate_code_quality(self, params: TechnicalParameters, complexity: float) -> float:
        """Estimate code quality score"""
        score = 0.8  # Base score for Algorand ASAs (standardized)

        # Adjust based on parameters
        if params.freeze_enabled or params.clawback_enabled:
            score -= 0.1  # Complexity penalty

        # Adjust based on complexity
        score -= complexity * 0.2

        return max(0.0, min(1.0, score))

    def _detect_upgrade_mechanism(self, params: TechnicalParameters) -> Optional[str]:
        """Detect if asset has upgrade mechanism"""
        if params.manager_address:
            return "manager_controlled"
        else:
            return "immutable"

    def _assess_community_standing(self, reputation_score: float, is_verified: bool) -> str:
        """Assess creator's community standing"""
        if is_verified and reputation_score >= 0.8:
            return "excellent"
        elif reputation_score >= 0.6:
            return "good"
        elif reputation_score >= 0.4:
            return "average"
        else:
            return "poor"

    def _default_technical_params(self) -> TechnicalParameters:
        """Default technical parameters for error cases"""
        return TechnicalParameters(
            total_supply=0,
            decimals=6,
            default_frozen=False,
            freeze_enabled=True,  # Assume worst case
            clawback_enabled=True,  # Assume worst case
            manager_address="unknown",
            reserve_address=None,
            freeze_address=None,
            clawback_address=None,
            url=None,
            metadata_hash=None
        )

    def _default_creator_analysis(self, asset_info: Dict) -> CreatorAnalysis:
        """Default creator analysis for error cases"""
        params = asset_info.get('params', {})
        creator_address = params.get('creator', 'unknown')

        return CreatorAnalysis(
            creator_address=creator_address,
            is_verified=False,
            reputation_score=0.0,
            previous_assets=[],
            governance_participation=False,
            community_standing="unknown",
            kyc_status=False,
            social_presence={}
        )

    async def _get_asset_info(self, asset_id: int) -> Optional[Dict]:
        """Get asset information from Algorand"""
        try:
            return self.algod_client.asset_info(asset_id)
        except Exception as e:
            self.logger.error(f"Error getting asset info for {asset_id}: {e}")
            return None