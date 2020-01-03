# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta,date
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class asignacion_presupuesto(models.Model):
    _name ='fiaes.asignacion.presupuesto'
    _inherit= ['mail.thread']
    name = fields.Char(string="Name")
    tipo = fields.Selection(selection=[('Refuerzo', 'Refuerzo')
                                        ,('Recorte', 'Recorte')
                                        ,('Reasignacion','Reasignacion')]
                                        , string='Tipo')
    state = fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Aprobado', 'Aprobado')]
                                        , string='Estado',default='Borrador',track_visibility=True)
    detalle_line= fields.One2many(comodel_name='fiaes.asignacion.presupuesto.detalle',inverse_name='asignacion_id')
    saldo = fields.Float("Total", compute='calcularTotal')
    x_fecha= fields.Date("actual",compute='fecha1')
 
    @api.one
    def fecha1(self):
        for r in self:
            day = date.today()
            r.x_fecha = day
                
    
    @api.one
    def presentar(self):
        for r in self:
            r.state='Aprobado'
            for d in r.detalle_line:
                plan=self.env['fiaes.planunidad'].search([('id','=',d.planunidad_id.id)],limit=1)
                monto=self.env['fiaes.planunidad.disponible'].search([('planunidad_id','=',d.planunidad_id.id),('proyecto_id','=',d.proyecto_id.id),('fuente_id','=',d.fuente_id.id)], limit=1)
                if monto:    
                    monto.monto= monto.monto + d.monto
                else:
                    dic={}
                    dic['planunidad_id']=d.planunidad_id.id
                    dic['proyecto_id']=d.proyecto_id.id
                    dic['fuente_id']=d.fuente_id.id
                    dic['monto']=d.monto
                    self.env['fiaes.planunidad.disponible'].create(dic)
            
            
    @api.depends('detalle_line')
    def calcularTotal(self):

        for r in self:
            total=0
            for detalle in r.detalle_line:
                total=total + detalle.monto
            
            r.saldo = total
            
    @api.one
    @api.constrains('detalle_line')
    def _check_refuerzo(self):
        for r in self:
            if r.tipo == 'Reasignacion':
                if r.saldo != 0:
                    raise ValidationError("El monto de reasignacion debe de ser 0")
    
class asignacion_refuerzo(models.Model):
    _name='fiaes.asignacion.presupuesto.detalle'
    name = fields.Char(string='Name')
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad')
    proyecto_id = fields.Many2one(string="Proyecto",comodel_name='project.project')
    fuente_id = fields.Many2one(string="Fuente",comodel_name='fiaes.fuente')  
    monto = fields.Float(string="Valor")
    asignacion_id = fields.Many2one(comodel_name='fiaes.asignacion.presupuesto')  
    tipo = fields.Selection(selection=[('Refuerzo', 'Refuerzo')
                                        ,('Recorte', 'Recorte')
                                        ,('Reasignacion','Reasignacion')]
                                        , string='Tipo', default="Refuerzo", related='asignacion_id.tipo')
  

    @api.one
    @api.constrains('monto', 'tipo')
    def _check_refuerzo_recorte(self):
        for r in self:
            if r.tipo=='Refuerzo':
                if r.monto< 0:
                    raise ValidationError("Los montos de refuerzo asignados no pueden ser negativos")
            if r.tipo == 'Recorte':
                if r.monto > 0:
                    raise ValidationError("Los montos de recortes asignados no pueden ser negativos")