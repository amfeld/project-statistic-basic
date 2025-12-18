from . import models
from . import wizard


def uninstall_hook(env):
    """
    Uninstall hook for project_statistic module.
    Odoo 18 automatically handles cleanup of fields, views, and database columns.
    """
    import logging
    _logger = logging.getLogger(__name__)
    _logger.info("Project Statistic module uninstall completed")