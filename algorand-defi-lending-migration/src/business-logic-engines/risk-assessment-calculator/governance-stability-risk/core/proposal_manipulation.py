"""
Proposal Manipulation Detection and Risk Assessment
Detects and analyzes potential governance proposal manipulation and attack vectors
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np
import re
from collections import defaultdict, Counter
import hashlib

class ManipulationType(Enum):
    """Types of proposal manipulation"""
    FLASH_GOVERNANCE = "flash_governance"
    VOTE_BUYING = "vote_buying"
    PROPOSAL_SPAM = "proposal_spam"
    COORDINATION_ATTACK = "coordination_attack"
    SOCIAL_ENGINEERING = "social_engineering"
    FAKE_PROPOSAL = "fake_proposal"
    TIMING_MANIPULATION = "timing_manipulation"
    CONTENT_MANIPULATION = "content_manipulation"

class ManipulationSeverity(Enum):
    """Severity levels for manipulation"""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    SUSPICIOUS = "suspicious"

@dataclass
class ProposalMetrics:
    """Metrics for a single proposal"""
    proposal_id: str
    title: str
    content_hash: str
    submission_time: datetime
    voting_deadline: datetime
    submitter_address: str

    # Voting metrics
    total_votes: int
    yes_votes: int
    no_votes: int
    abstain_votes: int
    voting_power_yes: float
    voting_power_no: float

    # Participation metrics
    unique_voters: int
    voter_addresses: Set[str]
    average_vote_timing: float
    voting_pattern_entropy: float

    # Content metrics
    content_complexity_score: float
    technical_depth_score: float
    urgency_indicators: List[str]

    # Financial implications
    financial_impact_score: float
    fund_allocation_amount: float
    affected_stakeholders: List[str]

@dataclass
class ManipulationIndicator:
    """Individual manipulation indicator"""
    indicator_type: str
    severity: ManipulationSeverity
    confidence_score: float
    evidence: List[str]
    affected_proposals: List[str]
    detection_method: str
    timestamp: datetime

@dataclass
class ProposalManipulationReport:
    """Comprehensive proposal manipulation report"""
    timestamp: datetime
    analyzed_proposals: int
    manipulation_indicators: List[ManipulationIndicator]
    high_risk_proposals: List[str]
    coordination_networks: List[Dict[str, Any]]
    risk_score: float
    recommendations: List[str]
    monitoring_alerts: List[str]

class ProposalManipulationDetector:
    """Detects and analyzes proposal manipulation attempts"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the proposal manipulation detector"""
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.proposal_history = []
        self.voting_patterns = defaultdict(list)
        self.known_manipulation_patterns = self._load_manipulation_patterns()
        self.suspicious_addresses = set()

    def _load_manipulation_patterns(self) -> Dict[str, Any]:
        """Load known manipulation patterns and signatures"""
        return {
            'flash_governance_indicators': [
                'urgent', 'emergency', 'immediate', 'asap', 'critical timing',
                'market opportunity', 'limited time', 'first mover'
            ],
            'vote_buying_patterns': [
                'guaranteed returns', 'profit sharing', 'rewards for voting',
                'vote and earn', 'compensation for participation'
            ],
            'social_engineering_terms': [
                'everyone is doing it', 'consensus reached', 'community agrees',
                'obvious choice', 'no-brainer', 'clear winner'
            ],
            'coordination_signals': [
                'coordinate', 'organize', 'synchronize', 'simultaneous',
                'planned voting', 'voting bloc', 'alliance'
            ]
        }

    async def analyze_proposal_manipulation(self,
                                          proposals_data: List[Dict[str, Any]],
                                          voting_data: Dict[str, Any]) -> ProposalManipulationReport:
        """
        Analyze proposals for manipulation indicators

        Args:
            proposals_data: List of proposal data
            voting_data: Associated voting data

        Returns:
            ProposalManipulationReport: Comprehensive manipulation analysis
        """
        try:
            self.logger.info(f"Analyzing {len(proposals_data)} proposals for manipulation")

            # Process proposal metrics
            proposal_metrics = await self._process_proposals(proposals_data, voting_data)

            # Detect manipulation indicators
            manipulation_indicators = await self._detect_manipulation_indicators(proposal_metrics)

            # Identify high-risk proposals
            high_risk_proposals = self._identify_high_risk_proposals(proposal_metrics, manipulation_indicators)

            # Analyze coordination networks
            coordination_networks = await self._analyze_coordination_networks(proposal_metrics, voting_data)

            # Calculate overall risk score
            risk_score = self._calculate_manipulation_risk_score(manipulation_indicators, coordination_networks)

            # Generate recommendations
            recommendations = self._generate_manipulation_recommendations(manipulation_indicators, risk_score)

            # Create monitoring alerts
            monitoring_alerts = self._create_monitoring_alerts(manipulation_indicators, high_risk_proposals)

            report = ProposalManipulationReport(
                timestamp=datetime.utcnow(),
                analyzed_proposals=len(proposals_data),
                manipulation_indicators=manipulation_indicators,
                high_risk_proposals=high_risk_proposals,
                coordination_networks=coordination_networks,
                risk_score=risk_score,
                recommendations=recommendations,
                monitoring_alerts=monitoring_alerts
            )

            self.logger.info(f"Manipulation analysis completed. Risk score: {risk_score:.2f}")
            return report

        except Exception as e:
            self.logger.error(f"Proposal manipulation analysis failed: {e}")
            raise

    async def _process_proposals(self,
                               proposals_data: List[Dict[str, Any]],
                               voting_data: Dict[str, Any]) -> List[ProposalMetrics]:
        """Process raw proposal data into structured metrics"""
        metrics_list = []

        try:
            for proposal_data in proposals_data:
                proposal_id = proposal_data.get('id', '')

                # Extract voting data for this proposal
                proposal_votes = voting_data.get(proposal_id, {})

                # Calculate content metrics
                content = proposal_data.get('content', '')
                content_metrics = self._analyze_proposal_content(content)

                # Calculate voting pattern metrics
                voting_metrics = self._analyze_voting_patterns(proposal_votes)

                # Calculate financial impact
                financial_metrics = self._analyze_financial_impact(proposal_data)

                metrics = ProposalMetrics(
                    proposal_id=proposal_id,
                    title=proposal_data.get('title', ''),
                    content_hash=hashlib.sha256(content.encode()).hexdigest(),
                    submission_time=datetime.fromisoformat(proposal_data.get('submission_time', datetime.utcnow().isoformat())),
                    voting_deadline=datetime.fromisoformat(proposal_data.get('voting_deadline', (datetime.utcnow() + timedelta(days=7)).isoformat())),
                    submitter_address=proposal_data.get('submitter', ''),

                    total_votes=proposal_votes.get('total_votes', 0),
                    yes_votes=proposal_votes.get('yes_votes', 0),
                    no_votes=proposal_votes.get('no_votes', 0),
                    abstain_votes=proposal_votes.get('abstain_votes', 0),
                    voting_power_yes=proposal_votes.get('voting_power_yes', 0),
                    voting_power_no=proposal_votes.get('voting_power_no', 0),

                    unique_voters=len(proposal_votes.get('voter_addresses', [])),
                    voter_addresses=set(proposal_votes.get('voter_addresses', [])),
                    average_vote_timing=voting_metrics.get('average_timing', 0),
                    voting_pattern_entropy=voting_metrics.get('entropy', 0),

                    content_complexity_score=content_metrics.get('complexity', 0),
                    technical_depth_score=content_metrics.get('technical_depth', 0),
                    urgency_indicators=content_metrics.get('urgency_indicators', []),

                    financial_impact_score=financial_metrics.get('impact_score', 0),
                    fund_allocation_amount=financial_metrics.get('allocation_amount', 0),
                    affected_stakeholders=financial_metrics.get('stakeholders', [])
                )

                metrics_list.append(metrics)

            return metrics_list

        except Exception as e:
            self.logger.error(f"Failed to process proposals: {e}")
            raise

    def _analyze_proposal_content(self, content: str) -> Dict[str, Any]:
        """Analyze proposal content for manipulation indicators"""
        try:
            if not content:
                return {'complexity': 0, 'technical_depth': 0, 'urgency_indicators': []}

            # Calculate complexity score
            word_count = len(content.split())
            sentence_count = len(re.split(r'[.!?]+', content))
            avg_sentence_length = word_count / max(sentence_count, 1)
            complexity_score = min(10, (word_count / 100) + (avg_sentence_length / 10))

            # Calculate technical depth
            technical_terms = ['algorithm', 'protocol', 'blockchain', 'consensus', 'cryptographic',
                             'smart contract', 'node', 'validator', 'stake', 'governance token']
            technical_count = sum(1 for term in technical_terms if term.lower() in content.lower())
            technical_depth = min(10, technical_count)

            # Detect urgency indicators
            urgency_indicators = []
            for pattern_list in self.known_manipulation_patterns.values():
                for pattern in pattern_list:
                    if pattern.lower() in content.lower():
                        urgency_indicators.append(pattern)

            return {
                'complexity': complexity_score,
                'technical_depth': technical_depth,
                'urgency_indicators': list(set(urgency_indicators))
            }

        except Exception as e:
            self.logger.error(f"Content analysis failed: {e}")
            return {'complexity': 0, 'technical_depth': 0, 'urgency_indicators': []}

    def _analyze_voting_patterns(self, proposal_votes: Dict[str, Any]) -> Dict[str, float]:
        """Analyze voting patterns for anomalies"""
        try:
            vote_timings = proposal_votes.get('vote_timings', [])

            if not vote_timings:
                return {'average_timing': 0, 'entropy': 0}

            # Calculate average voting timing
            avg_timing = np.mean(vote_timings)

            # Calculate entropy of voting pattern
            timing_buckets = np.histogram(vote_timings, bins=10)[0]
            timing_probabilities = timing_buckets / max(sum(timing_buckets), 1)
            entropy = -sum(p * np.log2(p + 1e-10) for p in timing_probabilities if p > 0)

            return {
                'average_timing': avg_timing,
                'entropy': entropy
            }

        except Exception as e:
            self.logger.error(f"Voting pattern analysis failed: {e}")
            return {'average_timing': 0, 'entropy': 0}

    def _analyze_financial_impact(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial impact and implications"""
        try:
            # Extract financial information
            fund_allocation = proposal_data.get('fund_allocation', 0)
            affected_protocols = proposal_data.get('affected_protocols', [])

            # Calculate impact score based on allocation size
            impact_score = min(10, fund_allocation / 1_000_000)  # Scale by millions

            return {
                'impact_score': impact_score,
                'allocation_amount': fund_allocation,
                'stakeholders': affected_protocols
            }

        except Exception as e:
            self.logger.error(f"Financial impact analysis failed: {e}")
            return {'impact_score': 0, 'allocation_amount': 0, 'stakeholders': []}

    async def _detect_manipulation_indicators(self,
                                            proposal_metrics: List[ProposalMetrics]) -> List[ManipulationIndicator]:
        """Detect manipulation indicators across proposals"""
        indicators = []

        try:
            # Flash governance detection
            flash_indicators = await self._detect_flash_governance(proposal_metrics)
            indicators.extend(flash_indicators)

            # Vote buying detection
            vote_buying_indicators = await self._detect_vote_buying(proposal_metrics)
            indicators.extend(vote_buying_indicators)

            # Proposal spam detection
            spam_indicators = await self._detect_proposal_spam(proposal_metrics)
            indicators.extend(spam_indicators)

            # Coordination attack detection
            coordination_indicators = await self._detect_coordination_attacks(proposal_metrics)
            indicators.extend(coordination_indicators)

            # Social engineering detection
            social_indicators = await self._detect_social_engineering(proposal_metrics)
            indicators.extend(social_indicators)

            # Timing manipulation detection
            timing_indicators = await self._detect_timing_manipulation(proposal_metrics)
            indicators.extend(timing_indicators)

            return indicators

        except Exception as e:
            self.logger.error(f"Manipulation detection failed: {e}")
            return []

    async def _detect_flash_governance(self, proposal_metrics: List[ProposalMetrics]) -> List[ManipulationIndicator]:
        """Detect flash governance attacks"""
        indicators = []

        try:
            flash_window = self.config.get('governance_risk', {}).get('proposal_risks', {}).get('flash_governance_window', 7200)
            min_deliberation = self.config.get('governance_risk', {}).get('proposal_risks', {}).get('minimum_deliberation_time', 172800)

            for proposal in proposal_metrics:
                evidence = []
                confidence = 0.0

                # Check deliberation time
                deliberation_time = (proposal.voting_deadline - proposal.submission_time).total_seconds()
                if deliberation_time < min_deliberation:
                    evidence.append(f"Insufficient deliberation time: {deliberation_time/3600:.1f} hours")
                    confidence += 30

                # Check urgency indicators in content
                if proposal.urgency_indicators:
                    evidence.append(f"Urgency indicators detected: {', '.join(proposal.urgency_indicators[:3])}")
                    confidence += 20

                # Check if multiple urgent proposals submitted quickly
                recent_proposals = [
                    p for p in proposal_metrics
                    if abs((p.submission_time - proposal.submission_time).total_seconds()) < flash_window
                    and p.proposal_id != proposal.proposal_id
                ]
                if len(recent_proposals) > 1:
                    evidence.append(f"Multiple proposals ({len(recent_proposals)}) in flash window")
                    confidence += 25

                # Check voting pattern (rapid voting after submission)
                if proposal.average_vote_timing < deliberation_time * 0.1:
                    evidence.append("Unusually rapid voting pattern detected")
                    confidence += 25

                if confidence >= 50:  # Threshold for flash governance detection
                    severity = ManipulationSeverity.CRITICAL if confidence >= 80 else ManipulationSeverity.HIGH

                    indicators.append(ManipulationIndicator(
                        indicator_type="FLASH_GOVERNANCE",
                        severity=severity,
                        confidence_score=min(100, confidence),
                        evidence=evidence,
                        affected_proposals=[proposal.proposal_id],
                        detection_method="temporal_analysis",
                        timestamp=datetime.utcnow()
                    ))

            return indicators

        except Exception as e:
            self.logger.error(f"Flash governance detection failed: {e}")
            return []

    async def _detect_vote_buying(self, proposal_metrics: List[ProposalMetrics]) -> List[ManipulationIndicator]:
        """Detect vote buying schemes"""
        indicators = []

        try:
            for proposal in proposal_metrics:
                evidence = []
                confidence = 0.0

                # Check for vote buying language in proposal content
                vote_buying_terms = self.known_manipulation_patterns.get('vote_buying_patterns', [])
                found_terms = [term for term in vote_buying_terms
                             if term.lower() in proposal.title.lower()]
                if found_terms:
                    evidence.append(f"Vote buying language detected: {', '.join(found_terms)}")
                    confidence += 40

                # Check for unusual voting power concentration
                if proposal.voting_power_yes > 0:
                    vote_power_ratio = proposal.voting_power_yes / max(proposal.unique_voters, 1)
                    if vote_power_ratio > 100_000:  # Unusually high power per voter
                        evidence.append(f"High voting power per voter: {vote_power_ratio:,.0f}")
                        confidence += 30

                # Check voting pattern entropy (low entropy suggests coordination)
                if proposal.voting_pattern_entropy < 2.0:  # Low entropy threshold
                    evidence.append(f"Low voting pattern entropy: {proposal.voting_pattern_entropy:.2f}")
                    confidence += 25

                # Check for suspicious voter addresses
                suspicious_voters = len(proposal.voter_addresses.intersection(self.suspicious_addresses))
                if suspicious_voters > 0:
                    evidence.append(f"Suspicious voter addresses involved: {suspicious_voters}")
                    confidence += suspicious_voters * 5

                if confidence >= 40:
                    severity = ManipulationSeverity.HIGH if confidence >= 70 else ManipulationSeverity.MODERATE

                    indicators.append(ManipulationIndicator(
                        indicator_type="VOTE_BUYING",
                        severity=severity,
                        confidence_score=min(100, confidence),
                        evidence=evidence,
                        affected_proposals=[proposal.proposal_id],
                        detection_method="pattern_analysis",
                        timestamp=datetime.utcnow()
                    ))

            return indicators

        except Exception as e:
            self.logger.error(f"Vote buying detection failed: {e}")
            return []

    async def _detect_proposal_spam(self, proposal_metrics: List[ProposalMetrics]) -> List[ManipulationIndicator]:
        """Detect proposal spam attacks"""
        indicators = []

        try:
            # Group proposals by submitter
            submitter_proposals = defaultdict(list)
            for proposal in proposal_metrics:
                submitter_proposals[proposal.submitter_address].append(proposal)

            # Check for spam patterns
            for submitter, proposals in submitter_proposals.items():
                if len(proposals) > 3:  # More than 3 proposals from same submitter
                    evidence = [f"Multiple proposals from same submitter: {len(proposals)}"]
                    confidence = min(80, len(proposals) * 15)

                    # Check for low-quality content
                    avg_complexity = np.mean([p.content_complexity_score for p in proposals])
                    if avg_complexity < 3.0:
                        evidence.append(f"Low average content complexity: {avg_complexity:.1f}")
                        confidence += 20

                    # Check for similar content (content hash analysis)
                    content_hashes = [p.content_hash for p in proposals]
                    unique_hashes = len(set(content_hashes))
                    if unique_hashes < len(proposals) * 0.8:  # Less than 80% unique
                        evidence.append(f"Similar content detected in multiple proposals")
                        confidence += 30

                    if confidence >= 50:
                        severity = ManipulationSeverity.MODERATE if confidence < 70 else ManipulationSeverity.HIGH

                        indicators.append(ManipulationIndicator(
                            indicator_type="PROPOSAL_SPAM",
                            severity=severity,
                            confidence_score=min(100, confidence),
                            evidence=evidence,
                            affected_proposals=[p.proposal_id for p in proposals],
                            detection_method="frequency_analysis",
                            timestamp=datetime.utcnow()
                        ))

            return indicators

        except Exception as e:
            self.logger.error(f"Proposal spam detection failed: {e}")
            return []

    async def _detect_coordination_attacks(self, proposal_metrics: List[ProposalMetrics]) -> List[ManipulationIndicator]:
        """Detect coordinated attack patterns"""
        indicators = []

        try:
            # Analyze voter overlap between proposals
            for i, proposal1 in enumerate(proposal_metrics):
                for proposal2 in proposal_metrics[i+1:]:
                    voter_overlap = len(proposal1.voter_addresses.intersection(proposal2.voter_addresses))
                    total_unique_voters = len(proposal1.voter_addresses.union(proposal2.voter_addresses))

                    if total_unique_voters > 0:
                        overlap_ratio = voter_overlap / total_unique_voters

                        if overlap_ratio > 0.7:  # High voter overlap
                            evidence = [f"High voter overlap between proposals: {overlap_ratio:.1%}"]
                            confidence = overlap_ratio * 60

                            # Check timing correlation
                            time_diff = abs((proposal1.submission_time - proposal2.submission_time).total_seconds())
                            if time_diff < 3600:  # Within 1 hour
                                evidence.append(f"Proposals submitted within {time_diff/60:.0f} minutes")
                                confidence += 20

                            # Check similar voting patterns
                            if abs(proposal1.voting_pattern_entropy - proposal2.voting_pattern_entropy) < 0.5:
                                evidence.append("Similar voting pattern entropy")
                                confidence += 15

                            if confidence >= 50:
                                severity = ManipulationSeverity.HIGH if confidence >= 75 else ManipulationSeverity.MODERATE

                                indicators.append(ManipulationIndicator(
                                    indicator_type="COORDINATION_ATTACK",
                                    severity=severity,
                                    confidence_score=min(100, confidence),
                                    evidence=evidence,
                                    affected_proposals=[proposal1.proposal_id, proposal2.proposal_id],
                                    detection_method="correlation_analysis",
                                    timestamp=datetime.utcnow()
                                ))

            return indicators

        except Exception as e:
            self.logger.error(f"Coordination attack detection failed: {e}")
            return []

    async def _detect_social_engineering(self, proposal_metrics: List[ProposalMetrics]) -> List[ManipulationIndicator]:
        """Detect social engineering attempts"""
        indicators = []

        try:
            social_terms = self.known_manipulation_patterns.get('social_engineering_terms', [])

            for proposal in proposal_metrics:
                evidence = []
                confidence = 0.0

                # Check for social engineering language
                found_terms = [term for term in social_terms
                             if term.lower() in proposal.title.lower()]
                if found_terms:
                    evidence.append(f"Social engineering language: {', '.join(found_terms)}")
                    confidence += len(found_terms) * 15

                # Check for false consensus indicators
                if proposal.content_complexity_score < 2.0 and proposal.financial_impact_score > 5.0:
                    evidence.append("High financial impact with low content complexity")
                    confidence += 25

                # Check for bandwagon effects
                if proposal.yes_votes > proposal.no_votes * 10:  # Overwhelming yes votes
                    if proposal.unique_voters < 100:  # But low participation
                        evidence.append("Potential bandwagon effect with low participation")
                        confidence += 20

                if confidence >= 35:
                    severity = ManipulationSeverity.MODERATE if confidence < 60 else ManipulationSeverity.HIGH

                    indicators.append(ManipulationIndicator(
                        indicator_type="SOCIAL_ENGINEERING",
                        severity=severity,
                        confidence_score=min(100, confidence),
                        evidence=evidence,
                        affected_proposals=[proposal.proposal_id],
                        detection_method="linguistic_analysis",
                        timestamp=datetime.utcnow()
                    ))

            return indicators

        except Exception as e:
            self.logger.error(f"Social engineering detection failed: {e}")
            return []

    async def _detect_timing_manipulation(self, proposal_metrics: List[ProposalMetrics]) -> List[ManipulationIndicator]:
        """Detect timing-based manipulation"""
        indicators = []

        try:
            # Check for proposals submitted at unusual times
            for proposal in proposal_metrics:
                evidence = []
                confidence = 0.0

                # Check submission timing (weekends, holidays, unusual hours)
                submission_hour = proposal.submission_time.hour
                submission_day = proposal.submission_time.weekday()

                # Late night/early morning submissions (potential to avoid scrutiny)
                if submission_hour < 6 or submission_hour > 22:
                    evidence.append(f"Unusual submission time: {submission_hour:02d}:00")
                    confidence += 15

                # Weekend submissions
                if submission_day >= 5:  # Saturday or Sunday
                    evidence.append("Weekend submission")
                    confidence += 10

                # Check voting deadline timing
                deadline_hour = proposal.voting_deadline.hour
                if deadline_hour < 8 or deadline_hour > 20:
                    evidence.append(f"Unusual voting deadline: {deadline_hour:02d}:00")
                    confidence += 10

                # Check for strategic timing relative to other proposals
                conflicting_proposals = [
                    p for p in proposal_metrics
                    if (p.voting_deadline > proposal.submission_time and
                        p.submission_time < proposal.voting_deadline and
                        p.proposal_id != proposal.proposal_id)
                ]

                if len(conflicting_proposals) > 2:
                    evidence.append(f"Overlaps with {len(conflicting_proposals)} other active proposals")
                    confidence += 15

                if confidence >= 25:
                    severity = ManipulationSeverity.LOW if confidence < 40 else ManipulationSeverity.MODERATE

                    indicators.append(ManipulationIndicator(
                        indicator_type="TIMING_MANIPULATION",
                        severity=severity,
                        confidence_score=min(100, confidence),
                        evidence=evidence,
                        affected_proposals=[proposal.proposal_id],
                        detection_method="temporal_analysis",
                        timestamp=datetime.utcnow()
                    ))

            return indicators

        except Exception as e:
            self.logger.error(f"Timing manipulation detection failed: {e}")
            return []

    def _identify_high_risk_proposals(self,
                                    proposal_metrics: List[ProposalMetrics],
                                    manipulation_indicators: List[ManipulationIndicator]) -> List[str]:
        """Identify proposals with high manipulation risk"""
        high_risk_proposals = []

        try:
            # Create risk scores for each proposal
            proposal_risks = defaultdict(float)

            for indicator in manipulation_indicators:
                for proposal_id in indicator.affected_proposals:
                    severity_weight = {
                        ManipulationSeverity.CRITICAL: 10,
                        ManipulationSeverity.HIGH: 7,
                        ManipulationSeverity.MODERATE: 4,
                        ManipulationSeverity.LOW: 2,
                        ManipulationSeverity.SUSPICIOUS: 1
                    }

                    risk_score = (indicator.confidence_score / 100) * severity_weight.get(indicator.severity, 1)
                    proposal_risks[proposal_id] += risk_score

            # Identify high-risk proposals (risk score > 5.0)
            for proposal_id, risk_score in proposal_risks.items():
                if risk_score > 5.0:
                    high_risk_proposals.append(proposal_id)

            return high_risk_proposals

        except Exception as e:
            self.logger.error(f"High-risk proposal identification failed: {e}")
            return []

    async def _analyze_coordination_networks(self,
                                           proposal_metrics: List[ProposalMetrics],
                                           voting_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze potential coordination networks"""
        networks = []

        try:
            # Build voter network graph
            voter_connections = defaultdict(set)

            for proposal in proposal_metrics:
                voters = list(proposal.voter_addresses)
                # Connect voters who voted on the same proposal
                for i, voter1 in enumerate(voters):
                    for voter2 in voters[i+1:]:
                        voter_connections[voter1].add(voter2)
                        voter_connections[voter2].add(voter1)

            # Find clusters of highly connected voters
            processed_voters = set()

            for voter, connections in voter_connections.items():
                if voter in processed_voters:
                    continue

                if len(connections) >= 5:  # Minimum network size
                    # Find all connected voters
                    network_members = {voter}
                    to_process = list(connections)

                    while to_process:
                        current_voter = to_process.pop()
                        if current_voter not in network_members:
                            network_members.add(current_voter)
                            to_process.extend(voter_connections[current_voter] - network_members)

                    if len(network_members) >= 5:
                        # Calculate network statistics
                        total_connections = sum(len(voter_connections[member]) for member in network_members)
                        avg_connections = total_connections / len(network_members)

                        # Calculate proposal overlap
                        member_proposals = defaultdict(set)
                        for proposal in proposal_metrics:
                            for member in network_members:
                                if member in proposal.voter_addresses:
                                    member_proposals[member].add(proposal.proposal_id)

                        # Calculate average proposal overlap
                        overlaps = []
                        members_list = list(network_members)
                        for i, member1 in enumerate(members_list):
                            for member2 in members_list[i+1:]:
                                overlap = len(member_proposals[member1].intersection(member_proposals[member2]))
                                overlaps.append(overlap)

                        avg_overlap = np.mean(overlaps) if overlaps else 0

                        networks.append({
                            'network_id': f"network_{len(networks)}",
                            'members': list(network_members),
                            'size': len(network_members),
                            'avg_connections_per_member': avg_connections,
                            'avg_proposal_overlap': avg_overlap,
                            'risk_score': min(10, len(network_members) * 0.5 + avg_overlap),
                            'detected_at': datetime.utcnow()
                        })

                        processed_voters.update(network_members)

            return networks

        except Exception as e:
            self.logger.error(f"Coordination network analysis failed: {e}")
            return []

    def _calculate_manipulation_risk_score(self,
                                         manipulation_indicators: List[ManipulationIndicator],
                                         coordination_networks: List[Dict[str, Any]]) -> float:
        """Calculate overall manipulation risk score"""
        try:
            if not manipulation_indicators and not coordination_networks:
                return 0.0

            # Weight manipulation indicators
            indicator_scores = []
            for indicator in manipulation_indicators:
                severity_weight = {
                    ManipulationSeverity.CRITICAL: 10,
                    ManipulationSeverity.HIGH: 7,
                    ManipulationSeverity.MODERATE: 4,
                    ManipulationSeverity.LOW: 2,
                    ManipulationSeverity.SUSPICIOUS: 1
                }

                score = (indicator.confidence_score / 100) * severity_weight.get(indicator.severity, 1)
                indicator_scores.append(score)

            # Weight coordination networks
            network_scores = [network['risk_score'] for network in coordination_networks]

            # Combine scores
            total_indicator_score = sum(indicator_scores)
            total_network_score = sum(network_scores)

            # Normalize to 0-10 scale
            risk_score = min(10.0, (total_indicator_score * 0.7 + total_network_score * 0.3) /
                           max(len(manipulation_indicators) + len(coordination_networks), 1))

            return risk_score

        except Exception as e:
            self.logger.error(f"Risk score calculation failed: {e}")
            return 5.0

    def _generate_manipulation_recommendations(self,
                                             manipulation_indicators: List[ManipulationIndicator],
                                             risk_score: float) -> List[str]:
        """Generate recommendations based on detected manipulation"""
        recommendations = []

        try:
            # General recommendations based on risk score
            if risk_score >= 7.0:
                recommendations.extend([
                    "Implement emergency governance measures",
                    "Suspend high-risk proposals pending investigation",
                    "Enhance real-time monitoring of voting patterns"
                ])
            elif risk_score >= 4.0:
                recommendations.extend([
                    "Increase scrutiny of flagged proposals",
                    "Implement additional verification requirements",
                    "Monitor identified coordination networks"
                ])

            # Specific recommendations based on indicators
            indicator_types = {indicator.indicator_type for indicator in manipulation_indicators}

            if "FLASH_GOVERNANCE" in indicator_types:
                recommendations.append("Enforce minimum deliberation periods")
                recommendations.append("Implement proposal complexity requirements")

            if "VOTE_BUYING" in indicator_types:
                recommendations.append("Investigate unusual voting power patterns")
                recommendations.append("Implement voter verification mechanisms")

            if "PROPOSAL_SPAM" in indicator_types:
                recommendations.append("Implement proposal rate limiting")
                recommendations.append("Require proposal quality standards")

            if "COORDINATION_ATTACK" in indicator_types:
                recommendations.append("Monitor voter coordination patterns")
                recommendations.append("Implement anti-coordination measures")

            # Remove duplicates and limit
            recommendations = list(dict.fromkeys(recommendations))[:7]

            return recommendations

        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            return ["Review governance security measures"]

    def _create_monitoring_alerts(self,
                                manipulation_indicators: List[ManipulationIndicator],
                                high_risk_proposals: List[str]) -> List[str]:
        """Create monitoring alerts for detected manipulation"""
        alerts = []

        try:
            # Critical indicators
            critical_indicators = [i for i in manipulation_indicators
                                 if i.severity == ManipulationSeverity.CRITICAL]
            if critical_indicators:
                alerts.append(f"CRITICAL: {len(critical_indicators)} critical manipulation indicators detected")

            # High-risk proposals
            if high_risk_proposals:
                alerts.append(f"WARNING: {len(high_risk_proposals)} high-risk proposals identified")

            # Pattern-specific alerts
            flash_governance = [i for i in manipulation_indicators
                              if i.indicator_type == "FLASH_GOVERNANCE"]
            if flash_governance:
                alerts.append(f"ALERT: Flash governance attack detected in {len(flash_governance)} cases")

            coordination_attacks = [i for i in manipulation_indicators
                                  if i.indicator_type == "COORDINATION_ATTACK"]
            if coordination_attacks:
                alerts.append(f"ALERT: Coordination attack patterns detected")

            return alerts

        except Exception as e:
            self.logger.error(f"Alert creation failed: {e}")
            return ["System monitoring alert generation failed"]

# Export main classes
__all__ = ['ProposalManipulationDetector', 'ProposalManipulationReport', 'ManipulationIndicator', 'ManipulationType', 'ManipulationSeverity']