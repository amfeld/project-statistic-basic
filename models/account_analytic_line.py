from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to trigger project analytics recomputation when timesheets are created.
        """
        lines = super().create(vals_list)
        self._trigger_project_analytics_recompute(lines)
        return lines

    def write(self, vals):
        """
        Override write to trigger project analytics recomputation when timesheets are modified.
        Only triggers when relevant fields change.
        """
        result = super().write(vals)

        # Only trigger recompute if fields that affect project analytics changed
        if any(key in vals for key in ['account_id', 'unit_amount', 'amount', 'employee_id', 'is_timesheet']):
            self._trigger_project_analytics_recompute(self)

        return result

    def unlink(self):
        """
        Override unlink to trigger project analytics recomputation when timesheets are deleted.
        """
        # Trigger BEFORE deletion so we can still access the data
        self._trigger_project_analytics_recompute(self)
        return super().unlink()

    def _trigger_project_analytics_recompute(self, lines):
        """
        Trigger recomputation of project analytics when analytic lines (timesheets) change.

        Args:
            lines: Recordset of account.analytic.line records that changed
        """
        if not lines:
            return

        # Collect all unique analytic account IDs from the lines
        analytic_account_ids = set()
        for line in lines:
            if line.account_id:
                analytic_account_ids.add(line.account_id.id)

        if not analytic_account_ids:
            return

        # Use shared helper method from project.project model
        self.env['project.project'].trigger_recompute_for_analytic_accounts(analytic_account_ids)
