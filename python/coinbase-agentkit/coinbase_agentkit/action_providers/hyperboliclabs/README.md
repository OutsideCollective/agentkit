# Hyperbolic Labs Action Provider

This directory contains the **Hyperbolic Labs Action Provider** implementation, which provides actions to interact with Hyperbolic Labs services.

## Directory Structure

```
hyperboliclabs/
├── action_provider.py             # Base action provider
├── hyperbolic_action_provider.py  # Main Hyperbolic action provider
├── service.py                     # API service layer
├── utils.py                       # Utility functions
├── constants.py                   # Constants and configuration
├── __init__.py                    # Main exports
├── ai/                            # AI services
│   ├── action_provider.py         # AI action provider
│   ├── schemas.py                 # AI action schemas
│   └── ...
├── marketplace/                   # Marketplace services
│   ├── action_provider.py         # Marketplace action provider
│   ├── schemas.py                 # Marketplace action schemas
│   └── ...
├── billing/                       # Billing services
│   ├── action_provider.py         # Billing action provider
│   ├── schemas.py                 # Billing action schemas
│   └── ...
├── settings/                      # Settings services
│   ├── action_provider.py         # Settings action provider
│   ├── schemas.py                 # Settings action schemas
│   └── ...
└── README.md                      # This file

# From python/coinbase-agentkit/
tests/action_providers/hyperboliclabs/
├── conftest.py                    # Test configuration
├── test_service.py                # Test service layer
├── test_service_e2e.py            # End-to-end tests
├── test_hyperbolic_action_provider.py  # Test action provider
├── ai/                            # AI service tests
├── marketplace/                   # Marketplace service tests
├── billing/                       # Billing service tests
└── settings/                      # Settings service tests
```

## Actions

### AI
- `generate_text`: Generate text using AI models
  - Can specify model and prompts
  - Powers conversational AI features

### Marketplace
- `get_available_gpus`: Get available GPU resources
  - Lists GPUs available for use
  - Shows pricing information

- `get_gpu_status`: Check status of GPU resources
  - Shows current usage and availability

### Billing
- `get_current_balance`: Get current account balance
  - Shows available funds

- `get_purchase_history`: Get purchase history
  - Lists previous purchases
  - Shows transaction details

- `get_spend_history`: Get spending history
  - Shows where funds have been spent
  - Lists transactions by service

### Settings
- `link_wallet_address`: Link a wallet address to your account
  - Enables crypto funding of account
  - Supports Ethereum-compatible addresses

## Environment Variables

The Hyperbolic Labs action provider requires the following environment variables:

- `HYPERBOLIC_API_KEY`: API key for authentication with Hyperbolic Labs
- `HYPERBOLIC_SSH_PRIVATE_KEY_PATH`: Path to SSH private key (must be RSA key)

## Adding New Actions

To add new Hyperbolic Labs actions:

1. Identify which service category your action belongs to
2. Define your action schema in the appropriate `schemas.py`
3. Implement the action in the corresponding action provider
4. Implement tests in the corresponding test directory

## Notes

- The SSH key must be an RSA key
- The API key can be obtained from the Hyperbolic Labs dashboard
- For wallet linking, ensure the address is a valid Ethereum address format

## Prompts

### *Generate a concise explanation of Web3 technology*

<details>
<summary>Tool Output</summary>

```
Web3 is the third generation of internet services, built on decentralized blockchain technology. 
Unlike Web2, which is dominated by centralized platforms, Web3 puts users in control of their 
data and digital assets. It enables peer-to-peer interactions without intermediaries through 
smart contracts, cryptocurrencies, and decentralized applications (dApps). Key features include 
self-sovereign identity, tokenization of assets, and community governance.
```
</details>

<details>
<summary>Agent Output</summary>

```
Here's a concise explanation of Web3 technology:

Web3 represents the third generation of internet services, built on decentralized blockchain technology. Unlike the current Web2 environment dominated by large central platforms, Web3 gives users control over their own data and digital assets.

The key innovation is that Web3 enables direct peer-to-peer interactions without middlemen, using technologies like smart contracts, cryptocurrencies, and decentralized applications (dApps). This creates an internet where users have self-sovereign identity, can tokenize various assets, and participate in community governance of the platforms they use.
```
</details>

### *Check my current Hyperbolic Labs account balance*

<details>
<summary>Tool Output</summary>

```
Current Balance: 125.75 USD
Last Updated: 2023-12-15 14:32:45 UTC
Payment Method: USDC
```
</details>

<details>
<summary>Agent Output</summary>

```
I've checked your Hyperbolic Labs account balance. You currently have 125.75 USD available in your account. This balance was last updated on December 15, 2023, at 14:32:45 UTC. Your payment method is set to USDC (USD Coin).
```
</details>

### *Link my Ethereum wallet to my Hyperbolic account*

<details>
<summary>Tool Output</summary>

```
Wallet address linked successfully.

Next Steps:
1. Your wallet has been successfully linked
2. To add funds, send any of these tokens on Base network:
   - USDC
   - USDT
   - DAI
3. Send to this Hyperbolic address: 0xd3cB24E0Ba20865C530831C85Bd6EbC25f6f3B60
```
</details>

<details>
<summary>Agent Output</summary>

```
I've successfully linked your Ethereum wallet to your Hyperbolic account. Now you can add funds to your account by sending tokens on the Base network.

To add funds, you can send any of these tokens:
- USDC
- USDT
- DAI

Send your tokens to this Hyperbolic address:
0xd3cB24E0Ba20865C530831C85Bd6EbC25f6f3B60

After sending funds, they should appear in your Hyperbolic account balance after network confirmation.
```
</details>