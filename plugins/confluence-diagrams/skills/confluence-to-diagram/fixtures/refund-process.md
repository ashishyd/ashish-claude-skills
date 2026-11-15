# Customer Refund Process

Space: Payments Operations | Version 7 | Last updated 2026-10-02 by Payments Ops

## Overview

This page describes how a customer refund request is handled from the moment
Support receives it until the money is back with the customer.

## Roles

| Role | Team | Responsibility |
|---|---|---|
| Support Agent | Customer Support | Logs the request and checks the order |
| Refund Approver | Finance | Approves refunds over £500 |
| Payments Service | Engineering | Sends the refund to the card network |

## Process

1. The Support Agent logs the refund request in the ticketing tool.
2. The Support Agent checks the order exists and was paid.
3. If the order was not paid, the request is rejected and the customer is told why.
4. Refunds of £500 or less are approved by the Support Agent.
5. Refunds over £500 go to the Refund Approver, who approves or rejects within 2 working days.
6. Once approved, the Payments Service sends the refund to the card network.
7. The card network confirms settlement and the customer is emailed.

## Approval thresholds

| Amount | Approver |
|---|---|
| £500 or less | Support Agent |
| Over £500 | Refund Approver (Finance) |

## Refund statuses

| Status | Meaning |
|---|---|
| Requested | Logged by Support |
| Pending approval | Waiting for Finance |
| Approved | Ready to send |
| Rejected | Will not be refunded |
| Sent | Submitted to the card network |
| Settled | Money returned to the customer |

## Known issues

If the card network declines the refund, Payments Ops retries it manually.
