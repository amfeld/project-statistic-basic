from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    faktor_hfc = fields.Float(
        string='Faktor HFC',
        default=1.0,
        help="Hourly Forecast Correction Factor. This factor is used to adjust the booked hours for this employee. "
             "Default is 1.0 (no adjustment). For example, 0.8 means 80% of booked hours count towards adjusted calculations."
    )
