# -*- coding: utf-8 -*-
from odoo import models

class PosPaymentMethod(models.Model):
    _name = 'pos.payment'
    _inherit = ['pos.payment', 'dinger.mixin']
