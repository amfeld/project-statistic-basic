from odoo import models, fields, api, _
import logging
import json

_logger = logging.getLogger(__name__)


class ProjectAnalytics(models.Model):
    _inherit = 'project.project'
    _description = 'Project Analytics Extension'

    # Currency field for monetary widgets
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        store=True,
        readonly=True,
        help="Currency used for all monetary fields in this project. Automatically set from company currency."
    )

    client_name = fields.Char(
        string='Name of Client',
        related='partner_id.name',
        store=True,
        help="The customer/client this project is for. This is automatically filled from the project's partner."
    )
    head_of_project = fields.Char(
        string='Head of Project',
        related='user_id.name',
        store=True,
        help="The person responsible for managing this project. This is the project manager assigned to the project."
    )

    # Sequence for manual drag&drop sorting in list view
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Used for manual sorting in the project statistics list view. Lower numbers appear first."
    )

    # Data Availability Status
    has_analytic_account = fields.Boolean(
        string='Has Analytic Account',
        compute='_compute_financial_data',
        store=True,
        help="Indicates whether this project has a valid analytic account for financial tracking. If False, no financial data can be calculated."
    )
    analytic_status_display = fields.Char(
        string='Analytic Status',
        compute='_compute_analytic_status_display',
        store=False,
        help="Display text for analytic account status: 'Has Account' or 'No Account'"
    )
    data_availability_status = fields.Selection([
        ('available', 'Data Available'),
        ('no_analytic_account', 'No Analytic Account'),
    ], string='Data Status',
        compute='_compute_financial_data',
        store=True,
        help="Shows whether financial data is available for this project. 'No Analytic Account' means the project is not configured for financial tracking."
    )

    # Sales Order fields (from linked sale orders)
    sale_order_amount_net = fields.Float(
        string='Sales Orders (NET)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Total amount (NET) of all confirmed sales orders linked to this project. Only includes orders in 'sale' or 'done' state. If no sales orders are linked, uses manual_sales_order_amount_net as fallback."
    )
    manual_sales_order_amount_net = fields.Float(
        string='Manual Sales Order Amount (NET)',
        default=0.0,
        help="Fallback sales order amount for projects without linked sales orders. This value will be used if no sales orders are found."
    )
    has_sales_orders = fields.Boolean(
        string='Has Sales Orders',
        compute='_compute_financial_data',
        store=True,
        help="Indicates whether this project has linked sales orders. Used to show fallback indicators in views."
    )
    sale_order_tax_names = fields.Char(
        string='SO Tax Codes',
        compute='_compute_financial_data',
        store=True,
        help="Tax codes used in confirmed sales orders linked to this project. Multiple taxes are shown as comma-separated values."
    )

    # Customer Invoice fields - NET (without tax)
    customer_invoiced_amount_net = fields.Float(
        string='Invoiced Amount (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Net amount invoiced to customers (without VAT/tax). This is the base amount before taxes are added. Uses price_subtotal from invoice lines."
    )

    # Detailed breakdown of customer invoices
    customer_invoices_net = fields.Float(
        string='Customer Invoices (NET)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Outgoing invoices to customers (NET, positive amount). Only includes out_invoice type."
    )
    customer_credit_notes_net = fields.Float(
        string='Customer Credit Notes (NET)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Credit notes issued to customers (NET, stored as negative amount). Only includes out_refund type."
    )

    customer_paid_amount_net = fields.Float(
        string='Paid Amount (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Net amount actually paid by customers (without VAT/tax). Calculated proportionally based on invoice payment status."
    )
    customer_outstanding_amount_net = fields.Float(
        string='Outstanding Amount (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Net amount still owed by customers (without VAT/tax). This is Invoiced Net - Paid Net."
    )

    # Customer Invoice fields - GROSS (with tax)
    customer_invoiced_amount_gross = fields.Float(
        string='Invoiced Amount (Gross)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Gross amount invoiced to customers (with VAT/tax). This is the total amount including all taxes. Uses price_total from invoice lines."
    )
    customer_paid_amount_gross = fields.Float(
        string='Paid Amount (Gross)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Gross amount actually paid by customers (with VAT/tax). Calculated proportionally based on invoice payment status."
    )
    customer_outstanding_amount_gross = fields.Float(
        string='Outstanding Amount (Gross)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Gross amount still owed by customers (with VAT/tax). This is Invoiced Gross - Paid Gross."
    )

    # Vendor Bill fields - NET (without tax)
    vendor_bills_total_net = fields.Float(
        string='Vendor Bills (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Net amount of vendor bills (without VAT/tax). This is the base cost before taxes. Uses price_subtotal from bill lines."
    )

    # Detailed breakdown of vendor bills
    vendor_bills_net = fields.Float(
        string='Vendor Bills (NET)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Incoming bills from vendors (NET, positive amount). Only includes in_invoice type."
    )
    vendor_credit_notes_net = fields.Float(
        string='Vendor Credit Notes (NET)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Credit notes received from vendors (NET, stored as negative amount). Only includes in_refund type."
    )

    # Vendor Bill fields - GROSS (with tax)
    vendor_bills_total_gross = fields.Float(
        string='Vendor Bills (Gross)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Gross amount of vendor bills (with VAT/tax). This is the total cost including all taxes. Uses price_total from bill lines."
    )

    # Adjusted Vendor Bill field (with surcharge factor)
    adjusted_vendor_bill_amount = fields.Float(
        string='Adjusted Vendor Bills',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Vendor bills with surcharge factor applied. Formula: Vendor Bills (NET) × Surcharge Factor. "
             "Default surcharge factor is 1.30 (30% markup). Used in profit/loss calculations."
    )

    # Skonto (Cash Discount) fields
    customer_skonto_taken = fields.Float(
        string='Customer Cash Discounts (Skonto)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Cash discounts granted to customers for early payment (Gewährte Skonti). This reduces project revenue. Calculated from expense accounts 7300-7303 and liability account 2130."
    )
    vendor_skonto_received = fields.Float(
        string='Vendor Cash Discounts Received',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Cash discounts received from vendors for early payment (Erhaltene Skonti). This reduces project costs and increases profit. Calculated from income accounts 4730-4733 and asset account 2670."
    )

    # Labor/Timesheet fields
    total_hours_booked = fields.Float(
        string='Total Hours Booked',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Total hours logged in timesheets for this project (Gebuchte Stunden). This includes all timesheet entries from employees working on this project. Used to track resource utilization and calculate labor costs."
    )
    labor_costs = fields.Float(
        string='Labor Costs',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Total cost of labor based on timesheets (Personalkosten). Calculated from timesheet entries multiplied by employee hourly rates. This is a major component of internal project costs. NET amount (no VAT on internal labor)."
    )
    total_hours_booked_adjusted = fields.Float(
        string='Total Hours Booked (Adjusted)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Adjusted total hours based on employee HFC (Hourly Forecast Correction) factors. Formula: sum(hours * employee.faktor_hfc). This provides a more accurate forecast of actual work effort by adjusting for employee efficiency factors."
    )
    labor_costs_adjusted = fields.Float(
        string='Labor Costs (Adjusted)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Adjusted labor costs calculated using general hourly rate from system parameters. Formula: total_hours_booked_adjusted * general_hourly_rate. Default rate is 66 EUR per hour. This provides standardized cost calculation across all employees."
    )

    # Other Cost fields
    other_costs_net = fields.Float(
        string='Other Costs (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Other internal costs excluding labor and vendor bills (net amount without VAT). These are miscellaneous project expenses tracked via analytic lines."
    )

    # Total Cost fields - NET (without tax)
    total_costs_net = fields.Float(
        string='Total Costs (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Total internal project costs without tax (Nettokosten). Calculated as: Labor Costs + Other Costs (Net). Vendor bills are tracked separately. All amounts are NET (without VAT)."
    )

    # Summary fields - NET-based calculations
    profit_loss_net = fields.Float(
        string='Profit/Loss (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Project profitability based on NET amounts (Gewinn/Verlust Netto). Formula: (Invoiced Net - Customer Skonto) - (Vendor Bills Net - Vendor Skonto + Total Costs Net). Consistent NET-to-NET calculation for accurate accounting. A positive value indicates profit, negative indicates loss."
    )
    negative_difference_net = fields.Float(
        string='Losses (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Total project losses as a positive number, NET basis (Verluste Netto). This shows the absolute value of negative profit/loss. If profit/loss is positive, this field is 0. Useful for tracking and reporting total losses."
    )

    # Current Calculated Profit/Loss (using adjusted values)
    current_calculated_profit_loss = fields.Float(
        string='Current P&L (Calculated)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Current calculated profit/loss using adjusted cost components. "
             "Formula: Total Invoiced - Adjusted Vendor Bills - Adjusted Labor Costs - Adjusted Other Costs. "
             "This provides real-time profitability including cost adjustments."
    )

    @api.depends('has_analytic_account')
    def _compute_analytic_status_display(self):
        """
        Compute display text for analytic account status.
        Returns 'Has Account' or 'No Account' for better UX.
        """
        for project in self:
            if project.has_analytic_account:
                project.analytic_status_display = 'Has Account'
            else:
                project.analytic_status_display = 'No Account'

    @api.depends('account_id')
    def _compute_financial_data(self):
        """
        Compute all financial data for the project based on analytic account lines.
        Uses Odoo v18 analytic_distribution JSON field for project cost allocation.
        """
        # Cache system parameters and project plan ONCE for all projects (performance optimization)
        general_hourly_rate = float(
            self.env['ir.config_parameter'].sudo().get_param(
                'project_statistic.general_hourly_rate', default='66.0'
            )
        )
        vendor_bill_surcharge_factor = float(
            self.env['ir.config_parameter'].sudo().get_param(
                'project_statistic.vendor_bill_surcharge_factor', default='1.30'
            )
        )
        project_plan = self.env.ref('analytic.analytic_plan_projects', raise_if_not_found=False)

        for project in self:
            # Initialize all fields
            customer_invoiced_amount_net = 0.0
            customer_paid_amount_net = 0.0
            customer_outstanding_amount_net = 0.0
            customer_invoiced_amount_gross = 0.0
            customer_paid_amount_gross = 0.0
            customer_outstanding_amount_gross = 0.0
            customer_invoices_net = 0.0
            customer_credit_notes_net = 0.0

            vendor_bills_total_net = 0.0
            vendor_bills_total_gross = 0.0
            vendor_bills_net = 0.0
            vendor_credit_notes_net = 0.0
            adjusted_vendor_bill_amount = 0.0

            customer_skonto_taken = 0.0
            vendor_skonto_received = 0.0

            sale_order_amount_net = 0.0
            sale_order_tax_names = ''
            has_sales_orders = False

            total_hours_booked = 0.0
            labor_costs = 0.0
            other_costs_net = 0.0
            total_costs_net = 0.0

            profit_loss_net = 0.0
            negative_difference_net = 0.0
            current_calculated_profit_loss = 0.0

            # Get the analytic account for this project (simplified logic)
            analytic_account = project.account_id

            # Verify it belongs to the projects plan (if plan exists)
            if analytic_account and project_plan and analytic_account.plan_id != project_plan:
                _logger.warning(
                    f"Project '{project.name}' analytic account is not on Projects plan "
                    f"(Plan: {analytic_account.plan_id.name if analytic_account.plan_id else 'None'})"
                )
                analytic_account = None

            if not analytic_account:
                _logger.debug(f"Project '{project.name}' (ID: {project.id}) has no analytic account")
                # Set status fields
                project.has_analytic_account = False
                project.data_availability_status = 'no_analytic_account'

                # Set all fields to 0.0 (not -1.0) to indicate no data
                project.customer_invoiced_amount_net = 0.0
                project.customer_paid_amount_net = 0.0
                project.customer_outstanding_amount_net = 0.0
                project.customer_invoiced_amount_gross = 0.0
                project.customer_paid_amount_gross = 0.0
                project.customer_outstanding_amount_gross = 0.0
                project.customer_invoices_net = 0.0
                project.customer_credit_notes_net = 0.0
                project.vendor_bills_total_net = 0.0
                project.vendor_bills_total_gross = 0.0
                project.vendor_bills_net = 0.0
                project.vendor_credit_notes_net = 0.0
                project.adjusted_vendor_bill_amount = 0.0
                project.customer_skonto_taken = 0.0
                project.vendor_skonto_received = 0.0
                project.sale_order_amount_net = 0.0
                project.sale_order_tax_names = ''
                project.has_sales_orders = False
                project.total_hours_booked = 0.0
                project.labor_costs = 0.0
                project.other_costs_net = 0.0
                project.total_costs_net = 0.0
                project.profit_loss_net = 0.0
                project.negative_difference_net = 0.0
                project.current_calculated_profit_loss = 0.0
                continue

            # 1. Calculate Customer Invoices (Revenue) - Both NET and GROSS
            customer_data = self._get_customer_invoices_from_analytic(analytic_account)
            customer_invoiced_amount_net = customer_data['invoiced_net']
            customer_paid_amount_net = customer_data['paid_net']
            customer_invoiced_amount_gross = customer_data['invoiced_gross']
            customer_paid_amount_gross = customer_data['paid_gross']
            customer_invoices_net = customer_data['invoices_net']
            customer_credit_notes_net = customer_data['credit_notes_net']

            # 2. Calculate Vendor Bills (Direct Costs) - Both NET and GROSS
            vendor_data = self._get_vendor_bills_from_analytic(analytic_account)
            vendor_bills_total_net = vendor_data['total_net']
            vendor_bills_total_gross = vendor_data['total_gross']
            vendor_bills_net = vendor_data['bills_net']
            vendor_credit_notes_net = vendor_data['credit_notes_net']

            # 3. Calculate Skonto (Cash Discounts) from analytic lines
            skonto_data = self._get_skonto_from_analytic(analytic_account)
            customer_skonto_taken = skonto_data['customer_skonto']
            vendor_skonto_received = skonto_data['vendor_skonto']

            # 3a. Calculate Sales Order data (confirmed orders linked to project)
            sales_order_data = self._get_sales_order_data(project)
            sale_order_amount_net = sales_order_data['amount_net']
            sale_order_tax_names = sales_order_data['tax_names']
            has_sales_orders = sales_order_data['has_sales_orders']

            # 4. Calculate Labor Costs (Timesheets) - NET amount
            timesheet_data = self._get_timesheet_costs(analytic_account)
            total_hours_booked = timesheet_data['hours']
            labor_costs = timesheet_data['costs']
            total_hours_booked_adjusted = timesheet_data['adjusted_hours']

            # 4a. Calculate Adjusted Labor Costs using general hourly rate (cached above)
            labor_costs_adjusted = total_hours_booked_adjusted * general_hourly_rate

            # 4b. Calculate Adjusted Vendor Bill Amount using surcharge factor (cached above)
            adjusted_vendor_bill_amount = vendor_bills_total_net * vendor_bill_surcharge_factor

            # 5. Calculate Other Costs (non-timesheet, non-bill analytic lines) - NET amount
            other_costs_net = self._get_other_costs_from_analytic(analytic_account)

            # 6. Calculate totals
            customer_outstanding_amount_net = customer_invoiced_amount_net - customer_paid_amount_net
            customer_outstanding_amount_gross = customer_invoiced_amount_gross - customer_paid_amount_gross

            total_costs_net = labor_costs + other_costs_net

            # 7. Calculate Profit/Loss - NET basis (consistent comparison)
            # Formula: (Revenue NET - Customer Skonto) - (Vendor Bills NET - Vendor Skonto + Internal Costs NET)
            # This ensures we're comparing NET revenue to NET costs (apples to apples)
            adjusted_revenue_net = customer_invoiced_amount_net - customer_skonto_taken
            adjusted_vendor_costs_net = vendor_bills_total_net - vendor_skonto_received
            profit_loss_net = adjusted_revenue_net - (adjusted_vendor_costs_net + total_costs_net)
            negative_difference_net = abs(min(0, profit_loss_net))

            # 8. Calculate Current Calculated Profit/Loss using adjusted cost components
            # Formula: Total Invoiced - Adjusted Vendor Bills - Adjusted Labor Costs - Adjusted Other Costs
            current_calculated_profit_loss = (
                customer_invoiced_amount_net
                - adjusted_vendor_bill_amount
                - labor_costs_adjusted
                - other_costs_net
            )

            # Update status fields (data available)
            project.has_analytic_account = True
            project.data_availability_status = 'available'

            # Update all computed fields
            project.customer_invoiced_amount_net = customer_invoiced_amount_net
            project.customer_paid_amount_net = customer_paid_amount_net
            project.customer_outstanding_amount_net = customer_outstanding_amount_net
            project.customer_invoiced_amount_gross = customer_invoiced_amount_gross
            project.customer_paid_amount_gross = customer_paid_amount_gross
            project.customer_outstanding_amount_gross = customer_outstanding_amount_gross
            project.customer_invoices_net = customer_invoices_net
            project.customer_credit_notes_net = customer_credit_notes_net

            project.vendor_bills_total_net = vendor_bills_total_net
            project.vendor_bills_total_gross = vendor_bills_total_gross
            project.vendor_bills_net = vendor_bills_net
            project.vendor_credit_notes_net = vendor_credit_notes_net
            project.adjusted_vendor_bill_amount = adjusted_vendor_bill_amount

            project.customer_skonto_taken = customer_skonto_taken
            project.vendor_skonto_received = vendor_skonto_received

            project.sale_order_amount_net = sale_order_amount_net
            project.sale_order_tax_names = sale_order_tax_names
            project.has_sales_orders = has_sales_orders

            project.total_hours_booked = total_hours_booked
            project.labor_costs = labor_costs
            project.total_hours_booked_adjusted = total_hours_booked_adjusted
            project.labor_costs_adjusted = labor_costs_adjusted
            project.other_costs_net = other_costs_net
            project.total_costs_net = total_costs_net

            project.profit_loss_net = profit_loss_net
            project.negative_difference_net = negative_difference_net
            project.current_calculated_profit_loss = current_calculated_profit_loss

    def _get_customer_invoices_from_analytic(self, analytic_account):
        """Get customer invoices/credit notes via analytic_distribution. Returns NET and GROSS amounts."""
        result = {
            'invoiced_net': 0.0,
            'paid_net': 0.0,
            'invoiced_gross': 0.0,
            'paid_gross': 0.0,
            'invoices_net': 0.0,
            'credit_notes_net': 0.0,
        }

        # Find all posted customer invoice/credit note lines with this analytic account
        # RELAXED FILTER: Removed account_type filter to catch all invoice lines
        # German accounting (SKR03/SKR04) might use different account types
        invoice_lines = self.env['account.move.line'].search([
            ('analytic_distribution', '!=', False),
            ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
            ('display_type', 'not in', ['line_section', 'line_note']),  # Exclude section/note lines
        ])

        _logger.debug(f"Found {len(invoice_lines)} potential invoice lines")

        matched_lines = 0
        for line in invoice_lines:
            if not line.analytic_distribution:
                continue

            # Skip reversal entries (Storno) - they cancel out the original entry
            # In Odoo 18, only reversed_entry_id exists (reversal_move_id was removed)
            if line.move_id.reversed_entry_id:
                continue

            # Parse the analytic_distribution JSON
            try:
                distribution = line.analytic_distribution
                if isinstance(distribution, str):
                    distribution = json.loads(distribution)

                # Check if this project's analytic account is in the distribution
                if str(analytic_account.id) in distribution:
                    matched_lines += 1
                    # Get the percentage allocated to this project for THIS LINE
                    percentage = distribution.get(str(analytic_account.id), 0.0) / 100.0

                    # Get the invoice to calculate payment proportion
                    invoice = line.move_id

                    # Calculate this line's contribution to the project
                    # NET: price_subtotal (without taxes)
                    line_amount_net = line.price_subtotal * percentage
                    # GROSS: price_total (with taxes)
                    line_amount_gross = line.price_total * percentage

                    # Separate tracking for invoices vs credit notes
                    if invoice.move_type == 'out_invoice':
                        # Regular invoices: positive amounts
                        result['invoices_net'] += line_amount_net
                    elif invoice.move_type == 'out_refund':
                        # Credit notes: store as negative amounts
                        result['credit_notes_net'] += -abs(line_amount_net)
                        # For total calculation, make credit notes negative
                        line_amount_net = -abs(line_amount_net)
                        line_amount_gross = -abs(line_amount_gross)

                    result['invoiced_net'] += line_amount_net
                    result['invoiced_gross'] += line_amount_gross

                    _logger.debug(f"Invoice {invoice.name}: NET={line_amount_net:.2f}")

                    # Calculate paid amount for this line
                    # Payment proportion = (invoice.amount_total - invoice.amount_residual) / invoice.amount_total
                    if abs(invoice.amount_total) > 0:
                        payment_ratio = (invoice.amount_total - invoice.amount_residual) / invoice.amount_total
                        line_paid_net = line_amount_net * payment_ratio
                        line_paid_gross = line_amount_gross * payment_ratio
                        result['paid_net'] += line_paid_net
                        result['paid_gross'] += line_paid_gross

            except Exception as e:
                _logger.warning(f"Error parsing analytic_distribution for line {line.id}: {e}")
                continue

        _logger.debug(f"Matched {matched_lines} invoice lines for account {analytic_account.id}")

        return result

    def _get_vendor_bills_from_analytic(self, analytic_account):
        """Get vendor bills/refunds via analytic_distribution. Returns NET and GROSS amounts."""
        result = {
            'total_net': 0.0,
            'total_gross': 0.0,
            'bills_net': 0.0,
            'credit_notes_net': 0.0,
        }

        # Find all posted vendor bill/refund lines with this analytic account
        # RELAXED FILTER: Removed account_type filter to catch all bill lines
        # German accounting (SKR03/SKR04) might use different account types
        bill_lines = self.env['account.move.line'].search([
            ('analytic_distribution', '!=', False),
            ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', ['in_invoice', 'in_refund']),
            ('display_type', 'not in', ['line_section', 'line_note']),  # Exclude section/note lines
        ])

        _logger.debug(f"Found {len(bill_lines)} potential bill lines")

        matched_lines = 0
        for line in bill_lines:
            if not line.analytic_distribution:
                continue

            # Skip reversal entries (Storno) - they cancel out the original entry
            # In Odoo 18, only reversed_entry_id exists (reversal_move_id was removed)
            if line.move_id.reversed_entry_id:
                continue

            # Parse the analytic_distribution JSON
            try:
                distribution = line.analytic_distribution
                if isinstance(distribution, str):
                    distribution = json.loads(distribution)

                # Check if this project's analytic account is in the distribution
                if str(analytic_account.id) in distribution:
                    matched_lines += 1
                    # Get the percentage allocated to this project for THIS LINE
                    percentage = distribution.get(str(analytic_account.id), 0.0) / 100.0

                    # Get the bill to check type
                    bill = line.move_id

                    # Calculate this line's contribution to the project
                    # NET: price_subtotal (without taxes)
                    line_amount_net = line.price_subtotal * percentage
                    # GROSS: price_total (with taxes)
                    line_amount_gross = line.price_total * percentage

                    # Separate tracking for bills vs refunds
                    if bill.move_type == 'in_invoice':
                        # Regular vendor bills: positive amounts
                        result['bills_net'] += line_amount_net
                    elif bill.move_type == 'in_refund':
                        # Vendor refunds: store as negative amounts
                        result['credit_notes_net'] += -abs(line_amount_net)
                        # For total calculation, make refunds negative
                        line_amount_net = -abs(line_amount_net)
                        line_amount_gross = -abs(line_amount_gross)

                    result['total_net'] += line_amount_net
                    result['total_gross'] += line_amount_gross

                    _logger.debug(f"Bill {bill.name}: NET={line_amount_net:.2f}")

            except Exception as e:
                _logger.warning(f"Error parsing analytic_distribution for bill line {line.id}: {e}")
                continue

        _logger.debug(f"Matched {matched_lines} bill lines for account {analytic_account.id}")

        return result

    def _get_skonto_from_analytic(self, analytic_account):
        """Get cash discounts (Skonto) from German SKR03/SKR04 discount accounts."""
        result = {'customer_skonto': 0.0, 'vendor_skonto': 0.0}

        # Get all analytic lines for this account
        analytic_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', analytic_account.id)
        ])

        for line in analytic_lines:
            if not line.move_line_id or not line.move_line_id.account_id:
                continue

            account_code = line.move_line_id.account_id.code
            if not account_code:
                continue

            # Customer Skonto (Gewährte Skonti) - expense accounts 7300-7303 + liability 2130
            # These reduce our revenue/profit (customer got discount)
            if account_code.startswith(('7300', '7301', '7302', '7303', '2130')):
                result['customer_skonto'] += abs(line.amount)

            # Vendor Skonto (Erhaltene Skonti) - income accounts 4730-4733 + asset 2670
            # These increase our profit (we got discount from vendor)
            elif account_code.startswith(('4730', '4731', '4732', '4733', '2670')):
                result['vendor_skonto'] += abs(line.amount)

        return result

    def _get_timesheet_costs(self, analytic_account):
        """Get timesheet hours and costs. Returns adjusted hours based on employee HFC factors."""
        result = {'hours': 0.0, 'costs': 0.0, 'adjusted_hours': 0.0}

        # Find all timesheet lines for this analytic account
        timesheet_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', analytic_account.id),
            ('is_timesheet', '=', True)
        ])

        for line in timesheet_lines:
            hours = line.unit_amount or 0.0
            result['hours'] += hours
            result['costs'] += abs(line.amount or 0.0)

            # Calculate adjusted hours using employee HFC factor
            if line.employee_id and hasattr(line.employee_id, 'faktor_hfc'):
                faktor_hfc = line.employee_id.faktor_hfc or 1.0
                result['adjusted_hours'] += hours * faktor_hfc
            else:
                # If no employee or no HFC factor, use 1.0 (no adjustment)
                result['adjusted_hours'] += hours

        return result

    def _get_other_costs_from_analytic(self, analytic_account):
        """
        Get other costs excluding timesheets, invoices, bills, journal entries, and Skonto.
        Prevents double-counting by filtering out already-counted categories.
        """
        other_costs = 0.0

        # Skonto account codes (to exclude from other costs as they're counted separately)
        skonto_account_codes = ['7300', '7301', '7302', '7303', '2130', '4730', '4731', '4732', '4733', '2670']

        # Find all cost lines (negative amounts, not timesheets)
        # First get all potential cost lines
        cost_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', analytic_account.id),
            ('amount', '<', 0),
            ('is_timesheet', '=', False)
        ])

        _logger.debug(f"Analyzing other costs for account {analytic_account.id} ({analytic_account.name})")

        for line in cost_lines:
            should_include = True

            # Check if line has a move_line_id (comes from accounting entry)
            if line.move_line_id:
                move = line.move_line_id.move_id
                account = line.move_line_id.account_id

                # Skip if from any invoice or bill type
                if move:
                    move_type = move.move_type
                    if move_type in ['in_invoice', 'in_refund', 'out_invoice', 'out_refund']:
                        should_include = False

                    # Skip journal entries (type 'entry') - these include deferrals and other auto-generated entries
                    # Deferred expenses from vendor bills create journal entries that shouldn't be counted separately
                    # Real manual cost entries should be created directly as analytic lines without move_line_id
                    elif move_type == 'entry':
                        should_include = False

                    # Skip reversed entries to avoid counting cancellations twice
                    elif move.reversed_entry_id:
                        should_include = False

                # Skip Skonto/cash discount accounts (counted separately)
                if should_include and account and account.code in skonto_account_codes:
                    should_include = False

            if should_include:
                other_costs += abs(line.amount)

        _logger.debug(f"Total other costs for account {analytic_account.id}: {other_costs:.2f}")
        return other_costs

    def action_view_account_analytic_line(self):
        """
        Open analytic lines for this project with enhanced view showing NET amounts.
        Shows all account.analytic.line records associated with the project's analytic account.
        """
        self.ensure_one()

        # Get the analytic account
        # In Odoo 18, analytic_account_id was removed from projects, use account_id
        analytic_account = None
        if hasattr(self, 'account_id') and self.account_id:
            analytic_account = self.account_id

        if not analytic_account:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('No analytic account found for this project.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Get the custom list view using module-agnostic search
        list_view_id = False
        list_view = self.env['ir.ui.view'].search([
            ('name', '=', 'account.analytic.line.list.enhanced'),
            ('model', '=', 'account.analytic.line'),
        ], limit=1)
        if list_view:
            list_view_id = list_view.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Analytic Entries - %s') % self.name,
            'res_model': 'account.analytic.line',
            'view_mode': 'list,form',
            'views': [(list_view_id, 'list'), (False, 'form')],
            'domain': [('account_id', '=', analytic_account.id)],
            'context': {'default_account_id': analytic_account.id},
            'target': 'current',
        }

    def action_open_standard_project_form(self):
        """
        Open the standard Odoo project form view.
        Called from the analytics form view button.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'project.project',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': False,  # Use default project form view
            'target': 'current',
        }

    def action_view_account_moves(self):
        """
        Open account moves (invoices, bills, etc.) linked to this project via analytic distribution.
        This shows the actual journal entries/documents rather than analytic lines.
        """
        self.ensure_one()

        # Get the analytic account for this project
        analytic_account = self.account_id
        if not analytic_account:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('No analytic account found for this project.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Find all account.move.line records with this analytic account in distribution
        # Then get the unique parent moves
        move_lines = self.env['account.move.line'].search([
            ('analytic_distribution', '!=', False),
            ('parent_state', '=', 'posted'),
        ])

        # Filter for lines that have this analytic account
        move_ids = set()
        analytic_id_str = str(analytic_account.id)
        for line in move_lines:
            if line.analytic_distribution and analytic_id_str in line.analytic_distribution:
                move_ids.add(line.move_id.id)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Account Moves - %s') % self.name,
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', list(move_ids))],
            'context': {'search_default_posted': 1},
            'target': 'current',
        }

    def action_open_analytics_form(self):
        """
        Open the project analytics form view.
        Called from the standard project form view button.
        """
        self.ensure_one()

        # Get the analytics form view ID using multiple fallback methods
        view_id = False

        # Method 1: Try to get the view by searching for it by name (most reliable)
        view = self.env['ir.ui.view'].search([
            ('name', '=', 'project.project.form.account.analytics'),
            ('model', '=', 'project.project'),
        ], limit=1)
        if view:
            view_id = view.id
        else:
            # Method 2: Fallback to external ID lookup with module-agnostic search
            try:
                # Search for the external ID without module prefix
                imd = self.env['ir.model.data'].search([
                    ('name', '=', 'view_project_form_account_analytics'),
                    ('model', '=', 'ir.ui.view'),
                ], limit=1)
                if imd:
                    view_id = imd.res_id
            except Exception as e:
                _logger.warning(f"Could not find analytics form view: {e}")

        return {
            'type': 'ir.actions.act_window',
            'name': _('Financial Analysis - %s') % self.name,
            'res_model': 'project.project',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': dict(self.env.context, form_view_initial_mode='readonly'),
        }

    def _get_sales_order_data(self, project):
        """
        Get sales order data for the project: total NET amount and tax codes.

        Only includes confirmed sales orders (state in ['sale', 'done']).
        Sales orders are linked via project_id field (standard Odoo field).

        FALLBACK: If no sales orders are found, uses manual_sales_order_amount_net field.

        Args:
            project: project.project record

        Returns:
            dict: {
                'amount_net': float,  # Total untaxed amount (price_subtotal) or manual fallback
                'tax_names': str,     # Comma-separated tax names
                'has_sales_orders': bool,  # Whether linked sales orders exist
            }
        """
        result = {
            'amount_net': 0.0,
            'tax_names': '',
            'has_sales_orders': False,
        }

        # Search for confirmed sales orders linked to this project
        # state='sale' means confirmed, 'done' means fully delivered
        sales_orders = self.env['sale.order'].search([
            ('project_id', '=', project.id),
            ('state', 'in', ['sale', 'done'])
        ])

        if not sales_orders:
            # FALLBACK: Use manual amount if no sales orders found
            result['amount_net'] = project.manual_sales_order_amount_net or 0.0
            result['has_sales_orders'] = False
            return result

        result['has_sales_orders'] = True

        # Collect tax names (use set to avoid duplicates)
        tax_names_set = set()

        # Calculate total NET amount
        for order in sales_orders:
            result['amount_net'] += order.amount_untaxed  # NET amount (without taxes)

            # Collect tax names from order lines
            for line in order.order_line:
                for tax in line.tax_id:
                    if tax.name:
                        tax_names_set.add(tax.name)

        # Convert set to comma-separated string
        if tax_names_set:
            result['tax_names'] = ', '.join(sorted(tax_names_set))

        return result

    def action_refresh_financial_data(self):
        """
        Manually refresh/recompute all financial data for selected projects.
        This is useful when invoices or analytic lines are added/modified.
        Reloads the view after calculation to show updated values.
        """
        self._compute_financial_data()

        # Return a reload action with notification
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'notification': {
                    'title': _('Financial Data Refreshed'),
                    'message': _('Financial data has been recalculated for %s project(s).') % len(self),
                    'type': 'success',
                    'sticky': False,
                }
            }
        }

    @api.model
    def trigger_recompute_for_analytic_accounts(self, analytic_account_ids):
        """
        Shared helper method for hooks to trigger project analytics recomputation.

        This method is called from both account.move.line and account.analytic.line hooks
        to avoid code duplication (~150 lines).

        Args:
            analytic_account_ids: Set or list of analytic account IDs to process

        Returns:
            int: Number of projects that were recomputed
        """
        if not analytic_account_ids:
            return 0

        try:
            # Get project plan reference once
            try:
                project_plan = self.env.ref('analytic.analytic_plan_projects', raise_if_not_found=False)
            except Exception as e:
                _logger.warning(f"Could not load project plan reference: {e}")
                return 0

            if not project_plan:
                _logger.debug("Project analytic plan not found - skipping recompute trigger")
                return 0

            # Batch-fetch all analytic accounts
            analytic_accounts = self.env['account.analytic.account'].browse(list(analytic_account_ids))

            # Filter for project plan accounts only
            project_analytic_accounts = analytic_accounts.filtered(
                lambda a: a.exists() and a.plan_id == project_plan
            )

            if not project_analytic_accounts:
                return 0

            # Find all projects linked to these analytic accounts in one query
            projects = self.search([
                ('account_id', 'in', project_analytic_accounts.ids)
            ])

            if not projects:
                return 0

            # Process projects in batches
            project_ids_list = projects.ids
            chunk_size = 100
            total_projects = len(project_ids_list)

            _logger.debug(f"Triggering recompute for {total_projects} project(s)")

            for i in range(0, total_projects, chunk_size):
                chunk = project_ids_list[i:i + chunk_size]
                chunk_projects = self.browse(chunk)

                try:
                    # CRITICAL: Invalidate cache first to ensure fresh data
                    chunk_projects.invalidate_recordset()

                    # Recompute financial data for this batch
                    chunk_projects._compute_financial_data()

                    _logger.debug(f"Recomputed financial data for {len(chunk_projects)} project(s)")

                except Exception as e:
                    _logger.error(
                        f"Error recomputing financial data for projects {chunk}: {e}",
                        exc_info=True
                    )
                    continue

            return total_projects

        except Exception as e:
            _logger.error(f"Error in trigger_recompute_for_analytic_accounts: {e}", exc_info=True)
            return 0
