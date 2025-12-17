from odoo import models, fields, api, _


class RefreshFinancialDataWizard(models.TransientModel):
    _name = 'refresh.financial.data.wizard'
    _description = 'Refresh Financial Data with General Hourly Rate'

    general_hourly_rate = fields.Float(
        string='General Hourly Rate (EUR)',
        required=True,
        default=lambda self: float(
            self.env['ir.config_parameter'].sudo().get_param(
                'project_statistic.general_hourly_rate', default='66.0'
            )
        ),
        help="General hourly rate used to calculate adjusted labor costs. "
             "Formula: Total Hours Booked (Adjusted) × General Hourly Rate = Labor Costs (Adjusted)"
    )

    vendor_bill_surcharge_factor = fields.Float(
        string='Vendor Bill Surcharge Factor',
        required=True,
        default=lambda self: float(
            self.env['ir.config_parameter'].sudo().get_param(
                'project_statistic.vendor_bill_surcharge_factor', default='1.30'
            )
        ),
        help="Surcharge factor applied to vendor bills. "
             "Formula: Adjusted Vendor Bill Amount = Vendor Bills (NET) × Surcharge Factor. "
             "Default: 1.30 (30% surcharge)"
    )

    def action_refresh_data(self):
        """
        Update the system parameter with the new hourly rate and refresh financial data.

        This method runs synchronously in the user's request context.
        Cache invalidation ensures we read the latest data from the database.
        """
        self.ensure_one()

        # Update the system parameters
        self.env['ir.config_parameter'].sudo().set_param(
            'project_statistic.general_hourly_rate',
            str(self.general_hourly_rate)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'project_statistic.vendor_bill_surcharge_factor',
            str(self.vendor_bill_surcharge_factor)
        )

        # Get the active project IDs from context
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            projects = self.env['project.project'].browse(active_ids)
        else:
            # If no specific projects selected, refresh all
            projects = self.env['project.project'].search([])

        # CRITICAL: Invalidate cache to ensure fresh data
        # This forces Odoo to read from DB instead of using cached values
        projects.invalidate_recordset()

        # Trigger recomputation
        # This happens within the current transaction and will be committed
        # when the wizard completes successfully
        projects._compute_financial_data()

        # Show success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Financial Data Refreshed'),
                'message': _('Financial data has been recalculated for %s project(s) with hourly rate %.2f EUR and vendor bill surcharge factor %.2f.') % (
                    len(projects), self.general_hourly_rate, self.vendor_bill_surcharge_factor
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
