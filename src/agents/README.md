# Sub-Agents — Build Your Own

This is where you create your specialised agents. Study `triage.py` — it's the reference implementation that shows the full pattern for creating an agent node, binding tools, and returning state updates.

## Available Tool Groups

Import these from `src.tools`:

| Group | Tools | Description |
|---|---|---|
| `ACCOUNT_TOOLS` | `get_account_details`, `get_account_limits`, `update_contact_info`, `get_account_status` | Account management |
| `CARD_TOOLS` | `list_cards`, `freeze_card`, `unfreeze_card`, `order_replacement_card`, `get_card_status` | Card operations |
| `TRANSACTION_TOOLS` | `get_transaction_history`, `get_transaction_details`, `dispute_transaction`, `get_dispute_status` | Transaction queries |
| `PAYMENT_TOOLS` | `get_payees`, `initiate_transfer`, `get_exchange_rate`, `get_standing_orders`, `cancel_standing_order` | Payments & transfers |
| `KYC_TOOLS` | `get_kyc_status`, `get_required_documents`, `submit_document`, `get_account_restrictions` | Identity & compliance |

You can also mix tools from different groups or use `ALL_TOOLS` if appropriate.

## Wiring Into the Graph

After creating your agent, integrate it in `src/graph.py`:

- **`agent_map`** — tells the routing function which graph node handles each agent name
- **`available_agents`** — tells the triage prompt which agents exist so it only routes to real ones

Study how the triage node is wired (nodes, conditional edges, tool execution) and follow the same pattern for your sub-agents.

## State Access

Your agent node receives the full `AgentState`:

- `state["messages"]` — Full conversation history
- `state["user_info"]` — Customer context (user_id, name, account_id, etc.)
- `state["current_agent"]` — Currently active agent name

Use `state["user_info"]["user_id"]` when calling tools that need a user ID.
