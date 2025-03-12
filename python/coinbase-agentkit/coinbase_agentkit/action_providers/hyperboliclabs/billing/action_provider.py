"""Hyperbolic Billing action provider.

This module provides actions for interacting with Hyperbolic billing services.
It includes functionality for checking balance and spend history.
"""

from typing import Any

from coinbase_agentkit.network import Network

from ...action_decorator import create_action
from ..action_provider import ActionProvider
from ..marketplace.service import MarketplaceService
from .schemas import (
    GetCurrentBalanceSchema,
    GetPurchaseHistorySchema,
    GetSpendHistorySchema,
)
from .service import BillingService
from .utils import (
    format_purchase_history,
    format_spend_history,
)


class BillingActionProvider(ActionProvider):
    """Provides actions for interacting with Hyperbolic billing.

    This provider enables interaction with the Hyperbolic billing services for balance
    and spend history. It requires an API key which can be provided directly or
    through the HYPERBOLIC_API_KEY environment variable.
    """

    def __init__(
        self,
        api_key: str | None = None,
    ):
        """Initialize the Hyperbolic billing action provider.

        Args:
            api_key: Optional API key for authentication. If not provided,
                    will attempt to read from HYPERBOLIC_API_KEY environment variable.

        Raises:
            ValueError: If API key is not provided and not found in environment.

        """
        super().__init__("hyperbolic_billing", [], api_key=api_key)
        self.billing = BillingService(self.api_key)
        self.marketplace = MarketplaceService(self.api_key)

    @create_action(
        name="get_current_balance",
        description="""
This tool retrieves your current Hyperbolic platform credit balance.

It does not take any inputs.

Example successful response:
    Your current Hyperbolic platform balance is $150.00.
    Purchase History:
    - $100.00 on January 15, 2024
    - $50.00 on December 30, 2023

Example error response:
    Error: API request failed
    Error: Invalid authentication credentials

Important notes:
- This shows platform credits only, NOT cryptocurrency wallet balances
- All amounts are shown in USD
- Purchase history is ordered from most recent to oldest
""",
        schema=GetCurrentBalanceSchema,
    )
    def get_current_balance(self, args: dict[str, Any]) -> str:
        """Retrieve current balance and purchase history from the account.

        Args:
            args (dict[str, Any]): Input arguments for the action.

        Returns:
            str: A message containing the action response or error details.

        """
        try:
            GetCurrentBalanceSchema(**args)

            response = self.billing.get_balance()

            balance_usd = float(response.credits) / 100
            output = [f"Your current Hyperbolic platform balance is ${balance_usd:.2f}."]

            return "\n".join(output)

        except Exception as e:
            return f"Error: Balance retrieval: {e!s}"

    @create_action(
        name="get_spend_history",
        description="""
This tool retrieves your GPU rental spending history from Hyperbolic platform.

It does not take any inputs.

Example successful response:
    === GPU Rental Spending Analysis ===

    Instance Rentals:
    - instance-123:
      GPU: NVIDIA A100 (Count: 2)
      Duration: 3600 seconds
      Cost: $25.00

    GPU Type Statistics:
    NVIDIA A100:
      Total Rentals: 2
      Total Time: 3600 seconds
      Total Cost: $25.00

    Total Spending: $25.00

Example error response:
    Error: API request failed

Important notes:
- All costs are in USD
- Duration is in seconds
- History includes all past rentals
""",
        schema=GetSpendHistorySchema,
    )
    def get_spend_history(self, args: dict[str, Any]) -> str:
        """Retrieve GPU rental spending history from the platform.

        Args:
            args (dict[str, Any]): Input arguments for the action.

        Returns:
            str: A message containing the action response or error details.

        """
        try:
            GetSpendHistorySchema(**args)

            response = self.marketplace.get_instance_history()

            if not response:
                return "Could not retrieve instance history. Please try again later."

            if not response.instance_history:
                return "No rental history found."

            return format_spend_history(response)

        except Exception as e:
            return f"Error: Spend history retrieval: {e!s}"

    @create_action(
        name="get_purchase_history",
        description="""
This tool retrieves your purchase history of Hyperbolic platform credits.

It does not take any inputs.

Example successful response:
    Purchase History (showing 5 most recent):
    - $100.00 on January 15, 2024
    - $50.00 on December 30, 2023
    - $75.00 on November 20, 2023

Example error response:
    Error: API request failed
    Error: Invalid authentication credentials
    Error: No previous purchases found

Important notes:
- This shows platform credit purchases only
- All amounts are shown in USD
- Purchase history is limited to 5 most recent by default
""",
        schema=GetPurchaseHistorySchema,
    )
    def get_purchase_history(self, args: dict[str, Any]) -> str:
        """Retrieve the purchase history of platform credits.

        Args:
            args (dict[str, Any]): Input arguments for the action.

        Returns:
            str: A message containing the action response or error details.

        """
        try:
            GetPurchaseHistorySchema(**args)

            history_response = self.billing.get_purchase_history()
            return format_purchase_history(history_response)

        except Exception as e:
            return f"Error: Purchase history retrieval: {e!s}"

    def supports_network(self, network: Network) -> bool:
        """Check if network is supported by Hyperbolic billing actions.

        Args:
            network (Network): The network to check support for.

        Returns:
            bool: Always True as Hyperbolic billing actions don't depend on blockchain networks.

        """
        return True


def hyperbolic_billing_action_provider(
    api_key: str | None = None,
) -> BillingActionProvider:
    """Create a new instance of the BillingActionProvider.

    Args:
        api_key: Optional API key for authentication. If not provided,
                will attempt to read from HYPERBOLIC_API_KEY environment variable.

    Returns:
        A new Billing action provider instance.

    Raises:
        ValueError: If API key is not provided and not found in environment.

    """
    return BillingActionProvider(api_key=api_key)
