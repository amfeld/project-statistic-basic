from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ProjectAnalytics(models.Model):
    _inherit = 'project.project'
    _description = 'Project Analytics Extension'

    # Related fields
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    client_name = fields.Char(related='partner_id.name', store=True)
    head_of_project = fields.Char(related='user_id.name', store=True)
    sequence = fields.Integer(default=10)

    # Status fields
    has_analytic_account = fields.Boolean(compute='_compute_financial_data', store=True)
    analytic_status_display = fields.Char(compute='_compute_analytic_status_display')
    data_availability_status = fields.Selection([
        ('available', 'Data Available'),
        ('no_analytic_account', 'No Analytic Account'),
    ], compute='_compute_financial_data', store=True)

    # Sales Order fields
    sale_order_amount_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    manual_sales_order_amount_net = fields.Float(default=0.0)
    has_sales_orders = fields.Boolean(compute='_compute_financial_data', store=True)
    sale_order_tax_names = fields.Char(compute='_compute_financial_data', store=True)

    # Customer Invoice fields - NET
    customer_invoiced_amount_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    customer_invoices_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    customer_credit_notes_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    customer_paid_amount_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    customer_outstanding_amount_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')

    # Customer Invoice fields - GROSS
    customer_invoiced_amount_gross = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    customer_paid_amount_gross = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    customer_outstanding_amount_gross = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')

    # Vendor Bill fields - NET
    vendor_bills_total_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    vendor_bills_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    vendor_credit_notes_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')

    # Vendor Bill fields - GROSS
    vendor_bills_total_gross = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    adjusted_vendor_bill_amount = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')

    # Skonto (Cash Discount) fields
    customer_skonto_taken = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    vendor_skonto_received = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')

    # Labor/Timesheet fields
    total_hours_booked = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    labor_costs = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    total_hours_booked_adjusted = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    labor_costs_adjusted = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')

    # Cost/Revenue fields
    other_costs_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    adjusted_other_costs = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    other_revenue_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    total_costs_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')

    # Profit/Loss fields
    profit_loss_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    negative_difference_net = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')
    current_calculated_profit_loss = fields.Float(compute='_compute_financial_data', store=True, aggregator='sum')

    @api.depends('has_analytic_account')
    def _compute_analytic_status_display(self):
        for project in self:
            project.analytic_status_display = 'Has Account' if project.has_analytic_account else 'No Account'

    def _reset_financial_fields(self):
        """Reset all financial fields to zero."""
        self.customer_invoiced_amount_net = 0.0
        self.customer_paid_amount_net = 0.0
        self.customer_outstanding_amount_net = 0.0
        self.customer_invoiced_amount_gross = 0.0
        self.customer_paid_amount_gross = 0.0
        self.customer_outstanding_amount_gross = 0.0
        self.customer_invoices_net = 0.0
        self.customer_credit_notes_net = 0.0
        self.vendor_bills_total_net = 0.0
        self.vendor_bills_total_gross = 0.0
        self.vendor_bills_net = 0.0
        self.vendor_credit_notes_net = 0.0
        self.adjusted_vendor_bill_amount = 0.0
        self.customer_skonto_taken = 0.0
        self.vendor_skonto_received = 0.0
        self.sale_order_amount_net = 0.0
        self.sale_order_tax_names = ''
        self.has_sales_orders = False
        self.total_hours_booked = 0.0
        self.total_hours_booked_adjusted = 0.0
        self.labor_costs = 0.0
        self.labor_costs_adjusted = 0.0
        self.other_costs_net = 0.0
        self.adjusted_other_costs = 0.0
        self.other_revenue_net = 0.0
        self.total_costs_net = 0.0
        self.profit_loss_net = 0.0
        self.negative_difference_net = 0.0
        self.current_calculated_profit_loss = 0.0

    @api.depends('account_id')
    def _compute_financial_data(self):
        """Compute all financial data from analytic account lines."""
        ICP = self.env['ir.config_parameter'].sudo()
        try:
            hourly_rate = float(ICP.get_param('project_statistic.general_hourly_rate', '66.0'))
        except (ValueError, TypeError):
            hourly_rate = 66.0
            _logger.warning("Invalid general_hourly_rate parameter, using default 66.0")
        try:
            surcharge = float(ICP.get_param('project_statistic.vendor_bill_surcharge_factor', '1.30'))
        except (ValueError, TypeError):
            surcharge = 1.30
            _logger.warning("Invalid vendor_bill_surcharge_factor parameter, using default 1.30")
        project_plan = self.env.ref('analytic.analytic_plan_projects', raise_if_not_found=False)

        for project in self:
            analytic = project.account_id
            if analytic and project_plan and analytic.plan_id != project_plan:
                analytic = None

            if not analytic:
                project.has_analytic_account = False
                project.data_availability_status = 'no_analytic_account'
                project._reset_financial_fields()
                continue

            project.has_analytic_account = True
            project.data_availability_status = 'available'

            # Get all financial data
            cust = self._get_move_lines_data(analytic, ['out_invoice', 'out_refund'])
            vend = self._get_move_lines_data(analytic, ['in_invoice', 'in_refund'])
            skonto = self._get_skonto(analytic)
            sales = self._get_sales_orders(project)
            timesheet = self._get_timesheets(analytic)
            other = self._get_other_amounts(analytic)

            # Customer data
            project.customer_invoiced_amount_net = cust['net']
            project.customer_invoiced_amount_gross = cust['gross']
            project.customer_paid_amount_net = cust['paid_net']
            project.customer_paid_amount_gross = cust['paid_gross']
            project.customer_invoices_net = cust['invoices']
            project.customer_credit_notes_net = cust['refunds']
            project.customer_outstanding_amount_net = cust['net'] - cust['paid_net']
            project.customer_outstanding_amount_gross = cust['gross'] - cust['paid_gross']

            # Vendor data
            project.vendor_bills_total_net = vend['net']
            project.vendor_bills_total_gross = vend['gross']
            project.vendor_bills_net = vend['invoices']
            project.vendor_credit_notes_net = vend['refunds']
            project.adjusted_vendor_bill_amount = vend['net'] * surcharge

            # Skonto
            project.customer_skonto_taken = skonto['customer']
            project.vendor_skonto_received = skonto['vendor']

            # Sales orders
            project.sale_order_amount_net = sales['amount']
            project.sale_order_tax_names = sales['taxes']
            project.has_sales_orders = sales['has_orders']

            # Labor
            project.total_hours_booked = timesheet['hours']
            project.total_hours_booked_adjusted = timesheet['adjusted']
            project.labor_costs = timesheet['costs']
            project.labor_costs_adjusted = timesheet['adjusted'] * hourly_rate

            # Other costs and revenue
            project.other_costs_net = other['costs']
            project.adjusted_other_costs = other['costs'] * surcharge
            project.other_revenue_net = other['revenue']
            project.total_costs_net = timesheet['costs'] + other['costs']

            # Profit/Loss calculation (includes other revenue)
            revenue = cust['net'] - skonto['customer'] + other['revenue']
            costs = vend['net'] - skonto['vendor'] + timesheet['costs'] + other['costs']
            project.profit_loss_net = revenue - costs
            project.negative_difference_net = abs(min(0, project.profit_loss_net))
            # Current P&L applies surcharge factor to vendor bills and other costs
            project.current_calculated_profit_loss = (
                cust['net'] + other['revenue']
                - (vend['net'] * surcharge)
                - (timesheet['adjusted'] * hourly_rate)
                - (other['costs'] * surcharge)
            )

    def _get_move_lines_data(self, analytic, move_types):
        """Get invoice/bill data from move lines with analytic distribution."""
        result = {'net': 0.0, 'gross': 0.0, 'paid_net': 0.0, 'paid_gross': 0.0, 'invoices': 0.0, 'refunds': 0.0}
        is_customer = 'out_invoice' in move_types

        lines = self.env['account.move.line'].search([
            ('analytic_distribution', '!=', False),
            ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', move_types),
            ('display_type', 'not in', ['line_section', 'line_note']),
        ])

        analytic_id = str(analytic.id)
        for line in lines:
            dist = line.analytic_distribution
            if not dist or analytic_id not in dist or line.move_id.reversed_entry_id:
                continue

            pct = dist.get(analytic_id, 0.0) / 100.0
            net = line.price_subtotal * pct
            gross = line.price_total * pct
            move = line.move_id

            is_refund = move.move_type in ['out_refund', 'in_refund']
            if is_refund:
                result['refunds'] -= abs(net)
                net, gross = -abs(net), -abs(gross)
            else:
                result['invoices'] += net

            result['net'] += net
            result['gross'] += gross

            if abs(move.amount_total) > 0:
                ratio = (move.amount_total - move.amount_residual) / move.amount_total
                result['paid_net'] += net * ratio
                result['paid_gross'] += gross * ratio

        return result

    def _get_skonto(self, analytic):
        """Get cash discounts from German SKR03/SKR04 accounts."""
        result = {'customer': 0.0, 'vendor': 0.0}
        CUSTOMER_CODES = ('7300', '7301', '7302', '7303', '2130')
        VENDOR_CODES = ('4730', '4731', '4732', '4733', '2670')

        for line in self.env['account.analytic.line'].search([('account_id', '=', analytic.id)]):
            if not line.move_line_id or not line.move_line_id.account_id:
                continue
            code = line.move_line_id.account_id.code or ''
            if code.startswith(CUSTOMER_CODES):
                result['customer'] += abs(line.amount)
            elif code.startswith(VENDOR_CODES):
                result['vendor'] += abs(line.amount)

        return result

    def _get_timesheets(self, analytic):
        """Get timesheet hours and costs with HFC adjustment."""
        result = {'hours': 0.0, 'costs': 0.0, 'adjusted': 0.0}

        for line in self.env['account.analytic.line'].search([
            ('account_id', '=', analytic.id),
            ('is_timesheet', '=', True)
        ]):
            hours = line.unit_amount or 0.0
            result['hours'] += hours
            result['costs'] += abs(line.amount or 0.0)
            hfc = getattr(line.employee_id, 'faktor_hfc', 1.0) or 1.0
            result['adjusted'] += hours * hfc

        return result

    def _get_other_amounts(self, analytic):
        """Get other costs and revenue excluding timesheets, invoices, bills, and Skonto."""
        SKONTO_CODES = {'7300', '7301', '7302', '7303', '2130', '4730', '4731', '4732', '4733', '2670'}
        EXCLUDED_TYPES = {'in_invoice', 'in_refund', 'out_invoice', 'out_refund', 'entry'}
        result = {'costs': 0.0, 'revenue': 0.0}

        for line in self.env['account.analytic.line'].search([
            ('account_id', '=', analytic.id),
            ('is_timesheet', '=', False)
        ]):
            if line.move_line_id:
                move = line.move_line_id.move_id
                account = line.move_line_id.account_id
                if move and (move.move_type in EXCLUDED_TYPES or move.reversed_entry_id):
                    continue
                if account and account.code in SKONTO_CODES:
                    continue
            if line.amount < 0:
                result['costs'] += abs(line.amount)
            elif line.amount > 0:
                result['revenue'] += line.amount

        return result

    def _get_sales_orders(self, project):
        """Get confirmed sales order data."""
        result = {'amount': 0.0, 'taxes': '', 'has_orders': False}

        orders = self.env['sale.order'].search([
            ('project_id', '=', project.id),
            ('state', 'in', ['sale', 'done'])
        ])

        if not orders:
            result['amount'] = project.manual_sales_order_amount_net or 0.0
            return result

        result['has_orders'] = True
        taxes = set()
        for order in orders:
            result['amount'] += order.amount_untaxed
            for line in order.order_line:
                taxes.update(t.name for t in line.tax_id if t.name)
        result['taxes'] = ', '.join(sorted(taxes))

        return result

    # Action methods
    def action_view_account_analytic_line(self):
        """Open analytic lines for this project."""
        self.ensure_one()
        if not self.account_id:
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'message': _('No analytic account found.'), 'type': 'warning'}}

        view = self.env['ir.ui.view'].search([
            ('name', '=', 'account.analytic.line.list.enhanced'),
            ('model', '=', 'account.analytic.line')
        ], limit=1)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Analytic Entries - %s') % self.name,
            'res_model': 'account.analytic.line',
            'view_mode': 'list,form',
            'views': [(view.id if view else False, 'list'), (False, 'form')],
            'domain': [('account_id', '=', self.account_id.id)],
            'context': {'default_account_id': self.account_id.id},
        }

    def action_open_standard_project_form(self):
        """Open standard project form."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'project.project',
            'res_id': self.id,
            'view_mode': 'form',
        }

    def action_view_account_moves(self):
        """Open account moves linked to this project via analytic distribution."""
        self.ensure_one()
        if not self.account_id:
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'message': _('No analytic account found.'), 'type': 'warning'}}

        # Use analytic lines to find linked moves (indexed by account_id)
        analytic_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', self.account_id.id),
            ('move_line_id', '!=', False),
        ])
        move_ids = analytic_lines.mapped('move_line_id.move_id').ids

        return {
            'type': 'ir.actions.act_window',
            'name': _('Account Moves - %s') % self.name,
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', move_ids)],
        }

    def action_open_analytics_form(self):
        """Open project analytics form."""
        self.ensure_one()
        view = self.env['ir.ui.view'].search([
            ('name', '=', 'project.project.form.account.analytics'),
            ('model', '=', 'project.project')
        ], limit=1)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Financial Analysis - %s') % self.name,
            'res_model': 'project.project',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(view.id if view else False, 'form')],
            'context': {'form_view_initial_mode': 'readonly'},
        }

    def action_refresh_financial_data(self):
        """Manually refresh financial data."""
        self._compute_financial_data()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'notification': {
                'title': _('Financial Data Refreshed'),
                'message': _('Recalculated for %s project(s).') % len(self),
                'type': 'success',
            }}
        }

    @api.model
    def trigger_recompute_for_analytic_accounts(self, analytic_account_ids):
        """Trigger recomputation for projects with given analytic accounts."""
        if not analytic_account_ids:
            return 0

        project_plan = self.env.ref('analytic.analytic_plan_projects', raise_if_not_found=False)
        if not project_plan:
            return 0

        accounts = self.env['account.analytic.account'].browse(list(analytic_account_ids))
        valid_accounts = accounts.filtered(lambda a: a.exists() and a.plan_id == project_plan)
        if not valid_accounts:
            return 0

        projects = self.search([('account_id', 'in', valid_accounts.ids)])
        if projects:
            projects.invalidate_recordset()
            projects._compute_financial_data()

        return len(projects)
