# -*- coding: utf-8 -*-
##############################################################################

from odoo import api, models, fields, _
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__) 

class reintegro(models.Model):
    _name='fiaes.reintegro'
    _inherit=['mail.thread']
    name=fields.Char("Plan",related='proyect_id.name')
    proyect_id = fields.Many2one(comodel_name='fiaes.ejecutora.proyecto',string='Proyecto ejecutora')
    monto = fields.Float(string="Monto total de reintegro")
    fecha=fields.Date(string="Fecha de reintegro")
    hijo_ids=fields.One2many(comodel_name='fiaes.desembolso.reintegro', inverse_name='papa_id')
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Reintegro', 'Reintegrar')]
                                        , string='Estado',default='Borrador')
    fecha = fields.Date(string="Fecha reintegro")
    #pack_id=fields.One2many(comodel_name='fiaes.ejecutora.proyecto.disponible.pack', inverse_name='reintegro_id')
    pack_desembolso_id = fields.Many2one(comodel_name='fiaes.ejecutora.desembolso')
    monto_total = fields.Float(string="Monto de reintegro")

    @api.one
    def iniciar_reintegro(self):
        for r in self:
            r.state='Reintegro'

    
    @api.one
    def iniciar_reintegrado(self):
        
        reintegro = 0.0
        for r in self:
            total = r.monto
            r.state='Reintegrado'
            
            #line = self.env['fiaes.compensacion.pack.proyecto.desembolso'].search([('projecto_ejecutora_id','=',r.proyect_id)],order="id asc", limit=1)
            #if line.monto_ejecutora != 0:
            #    reintegro = total - line.monto_ejecutora
            #r.monto_total = reintegro
            #if line.monto_ejecutora = 0:
            #    line_2


                    
    
    @api.one
    def revertir(self):
        for r in self:
            r.state='Borrador'

    @api.multi
    def generar_items(self):
        for r in self:
            total = r.monto
            _logger.info(str(total))
            if r.state == 'Borrador':
                if r.proyect_id:
                    _logger.info('condicion proyecto')
                    for a in r.proyect_id.pack_desembolso_ids:
                        if total > 0:
                            total_aplicar=0.0
                            if total > a.monto_ejecutora:
                                total_aplicar= a.monto_ejecutora
                            else:
                                total_aplicar = total

                            _logger.info('se cumplio la condicion ')
                            dic={}
                            dic["name"]=a.name
                            dic["proyect_id"]=a.projecto_ejecutora_id.id
                            dic["fecha_aplicacion"]=a.fecha_desembolso
                            dic["total_financiado"]=a.monto_ejecutora
                            dic["papa_id"]=r.id
                            
                            dic["monto_reintegro"]=total_aplicar

                            
                            self.env['fiaes.desembolso.reintegro'].create(dic)
                            total = total - total_aplicar

    @api.one
    @api.constrains('monto', 'state')
    def aplicar_integro(self):
        for r in self:
            if r.state == 'Reintegro':
                if r.proyect_id:
                    for a in r.proyect_id:
                        if r.monto > a.total_financiado :
                            raise ValidationError('El monto de reintegro no puede ser mayor al monto financiado'+' '+str(r.proyect_id.total_financiado))




class desembolso_reintegro(models.Model):
    _name='fiaes.desembolso.reintegro'
    _inherit=['mail.thread']
    name=fields.Char("Paquete de compensacion por proyecto y desembolsos")
    proyect_id = fields.Many2one(comodel_name='fiaes.ejecutora.proyecto',string='Proyecto ejecutora')
    fecha_aplicacion = fields.Date(string="Fecha aplicacion desembolso")
    total_financiado=fields.Float("Monto financiado")
    
    papa_id = fields.Many2one(comodel_name='fiaes.reintegro')

    monto_reintegro = fields.Float(string="Monto de reintegro")