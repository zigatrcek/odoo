# -*- coding: utf-8 -*-
from odoo import fields, models

class Partner(models.Model):
    _inherit = 'res.partner'

    # add new column to determine if a partner is an instructor
    instructor = fields.Boolean('Instructor', default=False)

    session_ids = fields.Many2many('openacademy.session',
        string='Attended Sessions', readonly=True)
