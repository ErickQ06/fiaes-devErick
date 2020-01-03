# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class poa(models.Model):
    _name='fiaes.poa'
    _inherit= ['mail.thread']
    _description='Plan operativo anual'
    name= fields.Char("Plan",track_visibility=True)
    anio= fields.Char("Anio",track_visibility=True)
    comentario=fields.Text("Comentario",track_visibility=True)
    
    project_line = fields.One2many(comodel_name='project.project', inverse_name='poa_id')
    objetivo_line = fields.One2many(comodel_name='fiaes.poaobjetivos', inverse_name='poa_id')
    planunidad_line = fields.One2many(comodel_name='fiaes.planunidad', inverse_name='poa_id') 
    
    ingresos=fields.One2many('fiaes.poa.ingreso','poa_id', 'Planes de ingresos',track_visibility=True)
    techos=fields.One2many('fiaes.poa.techo','poa_id', 'Planes de techos de gastos',track_visibility=True)


class plaunidad(models.Model):
    _name='fiaes.planunidad'
    _inherit= ['mail.thread']
    name=fields.Char('Plan de unidad',compute='compute_name')
    unidad = fields.Many2one(comodel_name='hr.department')
    responsable = fields.Many2many(comodel_name='res.users')
    poa_id = fields.Many2one(comodel_name='fiaes.poa', string="POA")
    objetivo_line = fields.One2many(comodel_name='fiaes.poaobjetivos', inverse_name='planunidad_id')
    disponible_line = fields.One2many(comodel_name='fiaes.planunidad.disponible',inverse_name='planunidad_id')
    total = fields.Float(string="Gasto presupuestado", compute="cant_total")
    disponible = fields.Float(string="Gasto disponible", compute="compute_disponible",store=False)
    disponible_actual=fields.Float(string="Gasto disponible", compute="compute_disponible",store=False)
    ejecutado=fields.Float("Monto ejecutado",compute="calcular_ejecutado",store=False)
    reporte_ids = fields.One2many(comodel_name='fiaes.reporteplanunidad',inverse_name='planunidad_id', string='Reporte')
    reporte_proyecto_ids = fields.One2many(comodel_name='fiaes.reporteproyecto', inverse_name='planunidad_id', string='ReporteProyecto')
    reporte_actividad_ids = fields.One2many(comodel_name='fiaes.reporteactividad',inverse_name='planunidad_id', string="ReporteActividad")
    
    
    
    @api.one
    @api.depends('unidad')
    def calcular_ejecutado(self):
        for r in self:
            total=0
            compras=self.env['purchase.order.line'].search([('planunidad_id','=',r.id),('state','in',('purchase','done'))])
            for c in compras:
                total=total+c.price_subtotal
            r.ejecutado=total
    
    @api.one
    @api.depends('objetivo_line')
    def cant_total(self):
        for r in self:
            total=0.0
            for a in r.objetivo_line:
                total=total+a.total
            r.total=total
    
    @api.one
    @api.depends('objetivo_line')
    def compute_disponible(self):
        for r in self:
            total=0.0
            disponible=self.env['fiaes.poa.techo'].search([('poa_id','=',r.poa_id.id),('state','=','Aprobado')],limit=1)
            if disponible:
                for d in disponible.techo_departamento_ids:
                    if d.deparment_id.id==r.unidad.id:
                        total=d.gasto_operativo
            r.disponible=total
            r.disponible_actual=r.disponible-r.total
    
    
    
    @api.one
    @api.depends('unidad','poa_id')
    def compute_name(self):
        for r in self:
            if r.poa_id:
                if r.unidad:
                    r.name=r.unidad.name+'('+r.poa_id.name+')'
            else:
                if r.unidad:
                    r.name=r.unidad.name

    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Presentado', 'Presentado')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado',required=True,default='Borrador',track_visibility=True)
    
    
    @api.one
    def aprobar(self):
        for r in self:
            for o in r.objetivo_line:
                for a in o.actividad_line:
                    task=self.env['project.task'].create({'project_id':a.proyecto.id,'name':a.name})
                    for sa in a.subactividades_line:
                        stask=self.env['project.task'].create({'project_id':a.proyecto.id,'name':sa.name,'parent_id':task.id})
            r.state='Aprobado'
    
    
    @api.one
    def regresar(self):
        for r in self:
            r.state='Borrador'
    
    @api.one
    def presentar(self):
        for r in self:
            r.state='Presentado'
    
    @api.one
    def cancelar(self):
        for r in self:
            r.state='Cancelado'

class proyecto(models.Model):
    _inherit='project.project'  
    poa_id = fields.Many2one(comodel_name='fiaes.poa', string="POA")
    total = fields.Float(string="Total", compute="compute_disponible",store=False)
    
    @api.one
    @api.depends('poa_id')
    def compute_disponible(self):
        for r in self:
            total=0.0
            disponible=self.env['fiaes.poaactividad'].search([('proyecto','=',r.id)])
            if disponible:
                for d in disponible:
                    total=d.total
            r.total=total