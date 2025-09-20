"""
Storage abstraction for Lending API
Simple storage implementation with database abstraction
"""

import json
import os
import aiofiles
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LoanStorage:
    """Storage handler for loan data"""

    def __init__(self, storage_type: str = "file"):
        self.storage_type = storage_type
        self.data_dir = os.getenv("LOAN_DATA_DIR", "./data")
        self.ensure_data_directory()
        logger.info(f"LoanStorage initialized with {storage_type} storage")

    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)

    def get_loan_file_path(self, loan_id: str) -> str:
        """Get file path for loan data"""
        return os.path.join(self.data_dir, f"loan_{loan_id}.json")

    def get_user_index_file_path(self) -> str:
        """Get file path for user index"""
        return os.path.join(self.data_dir, "user_index.json")

    async def store_loan(self, loan_id: str, loan_data: Dict[str, Any]) -> bool:
        """Store loan data"""
        try:
            # Store loan data
            loan_file_path = self.get_loan_file_path(loan_id)
            async with aiofiles.open(loan_file_path, 'w') as f:
                await f.write(json.dumps(loan_data, indent=2))

            # Update user index
            await self.update_user_index(loan_data.get("user_id"), loan_id)

            logger.info(f"Stored loan {loan_id} for user {loan_data.get('user_id')}")
            return True

        except Exception as e:
            logger.error(f"Failed to store loan {loan_id}: {e}")
            return False

    async def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve loan data"""
        try:
            loan_file_path = self.get_loan_file_path(loan_id)

            if not os.path.exists(loan_file_path):
                return None

            async with aiofiles.open(loan_file_path, 'r') as f:
                content = await f.read()
                return json.loads(content)

        except Exception as e:
            logger.error(f"Failed to retrieve loan {loan_id}: {e}")
            return None

    async def update_loan(self, loan_id: str, update_data: Dict[str, Any]) -> bool:
        """Update loan data"""
        try:
            # Get existing loan data
            existing_loan = await self.get_loan(loan_id)
            if not existing_loan:
                logger.warning(f"Loan {loan_id} not found for update")
                return False

            # Merge update data
            existing_loan.update(update_data)
            existing_loan["updated_at"] = datetime.utcnow().isoformat()

            # Store updated data
            return await self.store_loan(loan_id, existing_loan)

        except Exception as e:
            logger.error(f"Failed to update loan {loan_id}: {e}")
            return False

    async def get_user_loans(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all loans for a user"""
        try:
            user_index = await self.get_user_index()
            user_loan_ids = user_index.get(user_id, [])

            loans = []
            for loan_id in user_loan_ids:
                loan_data = await self.get_loan(loan_id)
                if loan_data:
                    loans.append(loan_data)

            # Sort by creation date (newest first)
            loans.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            return loans

        except Exception as e:
            logger.error(f"Failed to get loans for user {user_id}: {e}")
            return []

    async def get_user_index(self) -> Dict[str, List[str]]:
        """Get user to loans mapping"""
        try:
            index_file_path = self.get_user_index_file_path()

            if not os.path.exists(index_file_path):
                return {}

            async with aiofiles.open(index_file_path, 'r') as f:
                content = await f.read()
                return json.loads(content)

        except Exception as e:
            logger.error(f"Failed to get user index: {e}")
            return {}

    async def update_user_index(self, user_id: str, loan_id: str) -> bool:
        """Update user index with new loan"""
        try:
            user_index = await self.get_user_index()

            if user_id not in user_index:
                user_index[user_id] = []

            if loan_id not in user_index[user_id]:
                user_index[user_id].append(loan_id)

            # Save updated index
            index_file_path = self.get_user_index_file_path()
            async with aiofiles.open(index_file_path, 'w') as f:
                await f.write(json.dumps(user_index, indent=2))

            return True

        except Exception as e:
            logger.error(f"Failed to update user index: {e}")
            return False

    async def count_active_loans(self) -> int:
        """Count active loans across all users"""
        try:
            user_index = await self.get_user_index()
            active_count = 0

            for user_id, loan_ids in user_index.items():
                for loan_id in loan_ids:
                    loan_data = await self.get_loan(loan_id)
                    if loan_data and loan_data.get("status") in ["requested", "negotiating", "agreed", "executing"]:
                        active_count += 1

            return active_count

        except Exception as e:
            logger.error(f"Failed to count active loans: {e}")
            return 0

    async def search_loans(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search loans with filters"""
        try:
            all_loans = []
            user_index = await self.get_user_index()

            # Get all loans
            for user_id, loan_ids in user_index.items():
                for loan_id in loan_ids:
                    loan_data = await self.get_loan(loan_id)
                    if loan_data:
                        all_loans.append(loan_data)

            # Apply filters
            filtered_loans = all_loans

            if "status" in filters:
                filtered_loans = [loan for loan in filtered_loans if loan.get("status") == filters["status"]]

            if "user_id" in filters:
                filtered_loans = [loan for loan in filtered_loans if loan.get("user_id") == filters["user_id"]]

            if "min_amount" in filters:
                min_amount = filters["min_amount"]
                filtered_loans = [
                    loan for loan in filtered_loans
                    if loan.get("request_data", {}).get("amount", 0) >= min_amount
                ]

            if "max_amount" in filters:
                max_amount = filters["max_amount"]
                filtered_loans = [
                    loan for loan in filtered_loans
                    if loan.get("request_data", {}).get("amount", 0) <= max_amount
                ]

            if "collateral_type" in filters:
                collateral_type = filters["collateral_type"]
                filtered_loans = [
                    loan for loan in filtered_loans
                    if loan.get("request_data", {}).get("collateral_type") == collateral_type
                ]

            # Sort results
            sort_by = filters.get("sort_by", "created_at")
            sort_order = filters.get("sort_order", "desc")

            if sort_by in ["created_at", "updated_at"]:
                filtered_loans.sort(
                    key=lambda x: x.get(sort_by, ""),
                    reverse=(sort_order == "desc")
                )

            return filtered_loans

        except Exception as e:
            logger.error(f"Failed to search loans: {e}")
            return []

    async def cleanup_old_loans(self, days_old: int = 90) -> int:
        """Clean up old completed/failed loans"""
        try:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            cutoff_str = cutoff_date.isoformat()

            user_index = await self.get_user_index()
            cleaned_count = 0

            for user_id, loan_ids in user_index.items():
                remaining_loan_ids = []

                for loan_id in loan_ids:
                    loan_data = await self.get_loan(loan_id)
                    if not loan_data:
                        continue

                    # Keep active loans and recent loans
                    if (loan_data.get("status") not in ["completed", "failed"] or
                        loan_data.get("created_at", "") > cutoff_str):
                        remaining_loan_ids.append(loan_id)
                    else:
                        # Remove old loan file
                        try:
                            loan_file_path = self.get_loan_file_path(loan_id)
                            if os.path.exists(loan_file_path):
                                os.remove(loan_file_path)
                                cleaned_count += 1
                        except Exception as e:
                            logger.error(f"Failed to remove loan file {loan_id}: {e}")

                user_index[user_id] = remaining_loan_ids

            # Update user index
            index_file_path = self.get_user_index_file_path()
            async with aiofiles.open(index_file_path, 'w') as f:
                await f.write(json.dumps(user_index, indent=2))

            logger.info(f"Cleaned up {cleaned_count} old loans")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup old loans: {e}")
            return 0


# Database storage implementation (for future use)
class DatabaseLoanStorage(LoanStorage):
    """Database-based loan storage (placeholder for future implementation)"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        super().__init__("database")
        logger.warning("Database storage not implemented yet, falling back to file storage")

    # TODO: Implement database operations
    # - Use SQLAlchemy or similar ORM
    # - Implement proper schema with migrations
    # - Add indexes for performance
    # - Implement connection pooling
    # - Add backup and recovery procedures