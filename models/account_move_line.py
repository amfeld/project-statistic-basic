from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to trigger project analytics recomputation.
        Uses batch processing for better performance.
        """
        lines = super().create(vals_list)
        self._trigger_project_analytics_recompute(lines)
        return lines

    def write(self, vals):
        """
        Override write to trigger project analytics recomputation.
        Only triggers when relevant fields change.
        """
        result = super().write(vals)

        # Only trigger recompute if fields that affect project analytics changed
        if any(key in vals for key in ['analytic_distribution', 'price_subtotal', 'price_total', 'debit', 'credit', 'balance']):
            self._trigger_project_analytics_recompute(self)

        return result

    def unlink(self):
        """
        Override unlink to trigger project analytics recomputation.
        Captures project IDs before deletion.
        """
        # Trigger BEFORE deletion so we can still access the data
        self._trigger_project_analytics_recompute(self)
        return super().unlink()

    def _trigger_project_analytics_recompute(self, lines):
        """
        Trigger recomputation of project analytics when move lines with analytic distribution change.

        Args:
            lines: Recordset of account.move.line records that changed
        """
        if not lines:
            return

        # Filter lines that have analytic distribution
        lines_with_distribution = lines.filtered(lambda l: l.analytic_distribution)

        if not lines_with_distribution:
            return

        # Collect all analytic account IDs from analytic_distribution
        analytic_account_ids = set()

        for line in lines_with_distribution:
            try:
                for analytic_account_id_str in line.analytic_distribution.keys():
                    try:
                        analytic_account_id = int(analytic_account_id_str)
                        analytic_account_ids.add(analytic_account_id)
                    except (ValueError, TypeError):
                        continue
            except Exception as e:
                _logger.warning(f"Error parsing analytic_distribution for line {line.id}: {e}")
                continue

        if not analytic_account_ids:
            return

        # Use shared helper method from project.project model
        self.env['project.project'].trigger_recompute_for_analytic_accounts(analytic_account_ids)
