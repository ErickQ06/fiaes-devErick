# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class fuente(models.Model):
    _name='fiaes.fuente'
    _inherit= ['mail.thread']
    _description='Fuente de financiamiento'
    name= fields.Char("Fuente",track_visibility=True)
    codigo= fields.Char("Codigo",track_visibility=True)
    tipo=fields.Selection(selection=[('Tradicional', 'Tradicional')
                                    ,('Compensacion', 'Compensacion')
                                    ,('Otra', 'Otra')]
                                    , string='Tipo',required=True,default='Tradicional',track_visibility=True)
    account_id=fields.Many2one(comodel_name='account.account', string='Cuenta asociada',track_visibility=True)
    cuentabancaria_ids=fields.Many2many('res.partner.bank','fuente_cuenta_rel', string='Cuentas bancaria asociada asociada',track_visibility=True)
    conservacion_ids=fields.Many2many("fiaes.conservacion",track_visibility=True) 
    
    