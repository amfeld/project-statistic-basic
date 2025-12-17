from . import models
from . import wizard


def uninstall_hook(env):
    """
    Uninstall hook for project_statistic module.

    In Odoo 18, the ORM automatically cleans up fields when a module is uninstalled.
    We don't need to manually drop columns - this causes timing issues where Odoo
    tries to access fields after they've been dropped.

    This hook is kept minimal to just log the uninstallation.
    Odoo will automatically:
    - Remove ir.model.fields records for this module
    - Drop database columns for removed fields
    - Clean up view inheritances
    - Remove menu items and actions

    DO NOT manually drop columns or delete field records here - it breaks Odoo's cleanup!
    """
    import logging
    _logger = logging.getLogger(__name__)

    _logger.info("=" * 80)
    _logger.info("Project Statistic module uninstall hook started")
    _logger.info("=" * 80)
    _logger.info("Odoo 18 will automatically clean up:")
    _logger.info("  - All custom fields on project.project")
    _logger.info("  - All view inheritances")
    _logger.info("  - All menu items and actions")
    _logger.info("  - Database columns for removed fields")
    _logger.info("")
    _logger.info("No manual cleanup needed - Odoo handles everything!")
    _logger.info("=" * 80)
    _logger.info("Project Statistic module uninstall hook completed")
    _logger.info("=" * 80)

    # Let Odoo handle all cleanup automatically
    # DO NOT manually drop columns or delete fields - causes timing issues!