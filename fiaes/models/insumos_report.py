# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta,date
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__) 

class ReporteInsumos(models.Model):
    _name='fiaes.reporte.insumos'
    name= fields.Char(string="Name", compute='_compute_name')
    fecha = fields.Date(string="Fecha")
    planunidad_id=fields.Many2one(comodel_name='fiaes.planunidad')
    actividad_id = fields.Many2one(comodel_name='fiaes.poaactividad')
    hijo_id = fields.One2many(comodel_name='actividad.reporte', inverse_name='papa_id')
    disponible_line2 = fields.One2many(comodel_name='fiaes.asignacion.disponible',inverse_name='reasignacion_id')

    @api.one
    @api.depends('fecha')
    def _compute_name(self):
        for r in self:
            if r.planunidad_id:
                if r.fecha:
                    r.name=r.planunidad_id.name+' '+r.fecha.strftime("%m/%d/%Y")

    @api.multi
    def generate_items(self):
        for r in self:
            _logger.info('se cumplio la condicion del plan del R in self')
            for c in r.planunidad_id.objetivo_line:
                for actividad in c.actividad_line:
                    _logger.info('se cumplio la condicion del plan', str(1))
        #for r in self:
        #    _logger.info('R in self')
        #    for c in r.planunidad_id.objetivo_line:
        #        if c.actividad_line:
        #            _logger.info('Condicion del c'+ str(c.actividad_line))
        #        for actividad in c.actividad_line:
        #            _logger.info('condicion de la actividad'+str(actividad))
        #            line = self.env['fiaes.insumo'].search([('actividad_id','=',actividad.id)],limit=1)
        #            if line:
       #                 _logger.info('Se cumplio la condicion del insumo inicial'+str(line))
                    #if actividad.insumo_line:
                    #    _logger.info('Se cumplio la condicion del insumo')
                    #_logger.info('se cumplio la condicion del plan', str(1))
                    x=0
                    for insumo in actividad:
                        _logger.info('Se cumplio la condicion del insumo')
                        if insumo.extemp == False or insumo.deshabili == False:
                            _logger.info('Ultima condicion del insumo')
                            x=1
                    if x==1:
                        dic={}
                        dic["original_id"]=actividad.id
                        dic["name"]=actividad.name
                        dic["descripcion"]=actividad.descripcion
                        dic["proyecto"]=actividad.proyecto.id
                        dic["planunidad_id"]=actividad.planunidad_id.id
                        dic["fecha_inicial"]=actividad.fecha_inicial
                        dic["fecha_final"]=actividad.fecha_final
                        dic["deshabili"]=actividad.deshabili
                        dic["extemp"]=actividad.extemp
                        dic["papa_id"]=r.id
                        self.env['actividad.reporte'].create(dic)
                        for insumo in actividad.insumo_line:
                            if insumo.extemp == False or insumo.deshabili == False:
                                dic2={}
                                dic2['original_id']=insumo.id
                                dic2['preciouni']=insumo.preciouni
                                dic2['cantidad']=insumo.cantidad
                                dic2['extemp']=insumo.extemp
                                dic2['deshabili']=insumo.deshabili
                                dic2['report_id']=r.id
                                self.env['fiaes.insumo.copy.reporte'].create(dic2)

class InsumosPlanUnidad(models.Model):
    _name='actividad.reporte'
    _inherit=['mail.thread']
    name =  fields.Char(string="Actividad",track_visibility=True)
    descripcion = fields.Text(string="Descripcion",track_visibility=True)
    proyecto = fields.Many2one(comodel_name='project.project', string="Proyecto")
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad', string="Plan unidad",store=True)
    fecha_inicial=fields.Date("Fecha de inicio")
    fecha_final=fields.Date("Fecha de finalizacion")
    deshabili = fields.Boolean(string="Habilitado") 
    extemp = fields.Boolean(string="Extemporaneo")
    reasignacion_id = fields.Many2one(comodel_name='fiaes.reporte.insumos')
    papa_id = fields.Many2one(comodel_name='fiaes.reporte.insumos')
    insumo_id = fields.One2many(comodel_name='fiaes.insumo.copy.reporte', inverse_name='actividad_line')
    original_id = fields.Integer(string="id original")

class insumo(models.Model):
    _name = 'fiaes.insumo.copy.reporte'
    name = fields.Char(string="Bien/Servicio")
    categoria = fields.Many2one(comodel_name='fiaes.insumo.categoria', string='Categorias de insumos')
    actividad_line = fields.Many2one(comodel_name='actividad.reporte')
    preciouni = fields.Float(string="Precio Unitario")
    cantidad = fields.Float(string="Cantidad")
    total = fields.Float(string="Total", compute="cant_total",store=True)       
    extemp = fields.Boolean(string="Extemporaneo")
    deshabili = fields.Boolean(string="deshabilitado")
    report_id = fields.Many2one(comodel_name='fiaes.reporte.insumos')
    original_id = fields.Integer(string="id original")