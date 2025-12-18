from . import models
from . import wizard


def uninstall_hook(env):
    """
    Secure uninstall hook for project_statistic module.
    Cleans up module-specific system parameters and data.
    Odoo 18 ORM handles field/view/column cleanup automatically.
    """
    import logging
    _logger = logging.getLogger(__name__)

    _logger.info("Starting project_statistic module uninstall")

    # Clean up module-specific system parameters
    params_to_remove = [
        'project_statistic.general_hourly_rate',
        'project_statistic.vendor_bill_surcharge_factor',
    ]

    try:
        IrConfigParameter = env['ir.config_parameter'].sudo()
        for param in params_to_remove:
            param_record = IrConfigParameter.search([('key', '=', param)], limit=1)
            if param_record:
                param_record.unlink()
                _logger.debug(f"Removed system parameter: {param}")
    except Exception as e:
        _logger.warning(f"Could not remove system parameters: {e}")

    _logger.info("Project Statistic module uninstall completed")