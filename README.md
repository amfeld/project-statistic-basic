# Project Financial Analytics for Odoo v18 Enterprise

Real-time financial analytics module for Odoo v18 projects with NET/GROSS separation, German accounting (SKR03/SKR04), and Skonto tracking.

**Version:** 18.0.1.3.0
**License:** LGPL-3
**Compatibility:** Odoo v18 Enterprise / Odoo.sh

---

## Features

- **NET/GROSS separation** - Accurate profit calculation without VAT distortion
- **Customer invoices** - Track invoiced, paid, and outstanding amounts
- **Vendor bills** - External costs with surcharge factor
- **Labor costs** - Timesheet-based with HFC adjustment
- **Skonto tracking** - German cash discount accounts (SKR03/SKR04)
- **Profit/Loss** - Real-time project profitability

---

## Field Reference

### Status Fields

| Field | Type | Description |
|-------|------|-------------|
| `has_analytic_account` | Boolean | Project has valid analytic account |
| `data_availability_status` | Selection | `available` or `no_analytic_account` |
| `analytic_status_display` | Char | Display text: "Has Account" / "No Account" |

### Sales Order Fields

| Field | Calculation |
|-------|-------------|
| `sale_order_amount_net` | `sum(order.amount_untaxed)` for confirmed orders |
| `manual_sales_order_amount_net` | Fallback value if no sales orders linked |
| `has_sales_orders` | True if linked sales orders exist |
| `sale_order_tax_names` | Comma-separated tax names from order lines |

### Customer Invoice Fields (NET)

| Field | Calculation |
|-------|-------------|
| `customer_invoiced_amount_net` | `sum(line.price_subtotal * analytic_pct)` |
| `customer_paid_amount_net` | `invoiced_net * payment_ratio` |
| `customer_outstanding_amount_net` | `invoiced_net - paid_net` |
| `customer_invoices_net` | Only `out_invoice` (positive) |
| `customer_credit_notes_net` | Only `out_refund` (negative) |

### Customer Invoice Fields (GROSS)

| Field | Calculation |
|-------|-------------|
| `customer_invoiced_amount_gross` | `sum(line.price_total * analytic_pct)` |
| `customer_paid_amount_gross` | `invoiced_gross * payment_ratio` |
| `customer_outstanding_amount_gross` | `invoiced_gross - paid_gross` |

### Vendor Bill Fields

| Field | Calculation |
|-------|-------------|
| `vendor_bills_total_net` | `sum(line.price_subtotal * analytic_pct)` |
| `vendor_bills_total_gross` | `sum(line.price_total * analytic_pct)` |
| `vendor_bills_net` | Only `in_invoice` (positive) |
| `vendor_credit_notes_net` | Only `in_refund` (negative) |
| `adjusted_vendor_bill_amount` | `vendor_bills_total_net * surcharge_factor` |

### Skonto (Cash Discount) Fields

| Field | Accounts | Calculation |
|-------|----------|-------------|
| `customer_skonto_taken` | 7300-7303, 2130 | `sum(abs(line.amount))` |
| `vendor_skonto_received` | 4730-4733, 2670 | `sum(abs(line.amount))` |

### Labor/Timesheet Fields

| Field | Calculation |
|-------|-------------|
| `total_hours_booked` | `sum(line.unit_amount)` |
| `total_hours_booked_adjusted` | `sum(hours * employee.faktor_hfc)` |
| `labor_costs` | `sum(abs(line.amount))` from timesheets |
| `labor_costs_adjusted` | `adjusted_hours * general_hourly_rate` |

### Cost Fields

| Field | Calculation |
|-------|-------------|
| `other_costs_net` | Non-timesheet, non-invoice analytic costs |
| `total_costs_net` | `labor_costs + other_costs_net` |

### Profit/Loss Fields

| Field | Calculation |
|-------|-------------|
| `profit_loss_net` | `(invoiced_net - customer_skonto) - (vendor_bills_net - vendor_skonto + total_costs_net)` |
| `negative_difference_net` | `abs(min(0, profit_loss_net))` |
| `current_calculated_profit_loss` | `invoiced_net - adjusted_vendor_bills - adjusted_labor - other_costs` |

---

## System Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `project_statistic.general_hourly_rate` | 66.0 | EUR per hour for adjusted labor costs |
| `project_statistic.vendor_bill_surcharge_factor` | 1.30 | 30% markup on vendor bills |

---

## Calculation Formulas

### Payment Ratio
```python
payment_ratio = (move.amount_total - move.amount_residual) / move.amount_total
```

### Analytic Distribution
```python
# analytic_distribution is a JSON dict: {"account_id": percentage}
pct = distribution.get(str(analytic_account.id), 0.0) / 100.0
amount = line.price_subtotal * pct
```

### Profit/Loss (NET)
```python
revenue = customer_invoiced_amount_net - customer_skonto_taken
costs = vendor_bills_total_net - vendor_skonto_received + total_costs_net
profit_loss_net = revenue - costs
```

### Current P&L (Adjusted)
```python
current_calculated_profit_loss = (
    customer_invoiced_amount_net
    - (vendor_bills_total_net * surcharge_factor)
    - (total_hours_booked_adjusted * hourly_rate)
    - other_costs_net
)
```

---

## Technical Architecture

### Core Methods

| Method | Purpose |
|--------|---------|
| `_compute_financial_data()` | Main computation triggered by `account_id` changes |
| `_get_move_lines_data(analytic, move_types)` | Unified invoice/bill extraction |
| `_get_skonto(analytic)` | Cash discount from SKR03/SKR04 accounts |
| `_get_timesheets(analytic)` | Hours and costs with HFC adjustment |
| `_get_other_costs(analytic)` | Non-duplicate cost extraction |
| `_get_sales_orders(project)` | Confirmed sales order data |
| `trigger_recompute_for_analytic_accounts(ids)` | Hook trigger for auto-refresh |

### Automatic Triggers

Changes to these models trigger project recomputation:
- `account.move.line` - Invoice/bill changes
- `account.analytic.line` - Timesheet changes

### Excluded from Other Costs

To prevent double-counting:
- Timesheets (`is_timesheet=True`)
- Invoice/bill lines (`in_invoice`, `in_refund`, `out_invoice`, `out_refund`)
- Journal entries (`entry`)
- Reversed entries
- Skonto accounts

---

## Installation

### Requirements

- Odoo v18 Enterprise
- Analytic Accounting enabled
- Projects linked to analytic accounts

### Steps

1. Deploy module to Odoo.sh or addons directory
2. Apps → Install "Project Statistic"
3. Enable Analytic Accounting (Settings → Accounting)
4. Ensure projects have analytic accounts assigned

---

## Uninstall

The module includes a secure uninstall hook that:
- Removes system parameters (`project_statistic.*`)
- Odoo ORM handles field/column cleanup automatically

```
Apps → Project Statistic → Uninstall
```

---

## Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| Requires analytic accounting | No data without it | Enable in settings |
| Payment tracking is proportional | Estimate for multi-project invoices | Use 1 invoice per project |
| Skonto accounts hardcoded | SKR03/SKR04 only | Modify `_get_skonto()` |
| No multi-currency | Incorrect sums | Use single currency per project |
| Timesheet costs depend on HR config | Zero if not configured | Configure employee hourly rates |

---

## Testing

Run the test suite:

```bash
odoo-bin -c odoo.conf -d test_db -i project_statistic --test-enable --stop-after-init
```

### Test Cases

1. Project without analytic account
2. Customer invoice basic calculation
3. Vendor bill basic calculation
4. Customer Skonto tracking (7300 accounts)
5. Vendor Skonto tracking (4730 accounts)
6. Profit/loss calculation

---

## Changelog

### v18.0.1.3.0
- Simplified codebase following KISS principles (62% reduction)
- Unified `_get_move_lines_data()` method for invoices and bills
- Removed verbose help texts (documented in README)
- Secure uninstall hook with parameter cleanup
- Production-ready logging (debug level for loops)

### v18.0.1.2.1
- Added diagnostic scripts (removed in 1.3.0)
- German translation support

### v18.0.1.0.0
- Initial release for Odoo v18 Enterprise
