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
        _logger.info('se cumplio la condicion del plan al inicio')
        for r in self:
            _logger.info('se cumplio la condicion del plan del R in self')
            for c in r.planunidad_id.objetivo_line:
                for actividad in c.actividad_line:
                    _logger.info('se cumplio la condicion del plan', str(1))
                    x = 0
                    for insumo in actividad.insumo_line:
                        if insumo.extemp or insumo.deshabili:
                            x=1
                    _logger.info('se cumplio la condicion', str(x))
                    if x==1:
                        dic={}
                        dic["name"]=a.name
                        dic["descripcion"]=a.descripcion
                        dic["proyecto"] = a.proyecto.id
                        dic["planunidad_id"] = a.planunidad_id.id
                        dic["fecha_inicial"] = a.fecha_inicial
                        dic["fecha_final"] = a.fecha_final
                        dic["deshabili"] = a.deshabili
                        dic["extemp"] = a.extemp
                        dic["papa_id"] = r.id
                        self.env['actividad.reporte'].create(dic)
                        for insumo in actividad.insumo_line:
                            if insumo.extemp or insumo.deshabili:                    
                                _logger.info('se cumplio la condicion' +str(a.id) + str(line2.id))
                                dics={}
                                dics['name']=insumo.name
                                dics['categoria']=insumo.categoria.id
                                dics['actividad_id']=a.id
                                dics['preciouni']=insumo.preciouni
                                dics['cantidad']=insumo.cantidad
                                dics['extemp']=insumo.extemp
                                dics['deshabili']=insumo.deshabili
                                dics['actividad_line']=a.id
                                self.env['fiaes.insumo.copy.reporte'].create(dics)



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
