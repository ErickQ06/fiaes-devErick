# -*- coding: utf-8 -*-
##############################################################################

from odoo import api, models, fields, _
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID

class reintegro(models.Model):
    _name='fiaes.reintegro'
    _inherit=['mail.thread']
    name=fields.Char("Plan",related='projecto_id.name')
    proyect_id = fields.Many2one(comodel_name='fiaes.ejecutora.proyecto',string='Proyecto ejecutora')
    monto = fields.Float(string="Monto total de reintegro")
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Aplicado', 'Aplicado')
                                        ,('Reintegro', 'Reintegro iniciado')
                                        ,('Reintegrado', 'Reintegrado')]
                                        , string='Estado',default='Borrador')
    

    @api.one
    def iniciar_reintegro(self):
        for r in self:
            r.state='Reintegro'
