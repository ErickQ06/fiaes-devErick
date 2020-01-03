# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class objeto_conservacion(models.Model):
    _name='fiaes.conservacion'
    _inherit= ['mail.thread']
    _description='Objeto de conservacion'
    name= fields.Char("Objeto de conservacion",track_visibility=True)
    name_standard= fields.Char("Objeto de conservacion estandarizado",track_visibility=True)
    comentario=fields.Text("Comentario",track_visibility=True)    
    
    
class uet(models.Model):
    _name='fiaes.uet'
    _inherit= ['mail.thread']
    _description='UET'
    name= fields.Char("UET",track_visibility=True)
    comentario=fields.Text("Comentario",track_visibility=True)
    territorio_ids=fields.Many2many("fiaes.territorio",track_visibility=True)


class convocatoria(models.Model):
    _name='fiaes.convocatoria'
    _inherit= ['mail.thread']
    _description='Convocatoria de proyectos'
    name= fields.Char("Convocatoria",track_visibility=True)
    anio= fields.Char("Año",track_visibility=True)
    codigo=fields.Char("Codigo",track_visibility=True)
    comentario=fields.Text("Comentario",track_visibility=True)
    territorio_ids=fields.Many2many("fiaes.territorio",track_visibility=True)                                 
    conservacion_ids=fields.Many2many("fiaes.conservacion",track_visibility=True)
    state=fields.Selection(selection=[('Nueva', 'Nueva')
                                    ,('A Licitar', 'A Licitar')
                                    ,('Comprometida', 'Comprometida')
                                    ,('Finalizada', 'Finalizada')]
                                    , string='Estado',required=True,default='Nueva',track_visibility=True)
    
class producto(models.Model):
    _name='fiaes.producto'
    _inherit= ['mail.thread']
    _description='Productos'
    name= fields.Char("Producto",track_visibility=True)
    comentario=fields.Text("Comentario",track_visibility=True)
    conservacion_id=fields.Many2one("fiaes.conservacion",string="Objeto de conservacion",track_visibility=True)        
    indicador_ids=fields.Many2many("fiaes.indicador",track_visibility=True)  
    uom_id=fields.Many2one("uom.uom",string="Unidad de medida",track_visibility=True)
    
class tecnica(models.Model):
    _name='fiaes.tecnica'
    _inherit= ['mail.thread']
    _description='Tecnica de restauracion'
    name= fields.Char("Tecnica de restauracion",track_visibility=True)
    codigo= fields.Char("Codigo",track_visibility=True)
    comentario=fields.Text("Comentario",track_visibility=True)          
    
class categoria_insumo(models.Model):
    _name='fiaes.insumo.categoria'
    _inherit= ['mail.thread']
    _description='Categoria de insumo'
    name= fields.Char("Categoria de insumo",track_visibility=True)
    comentario=fields.Text("Comentario",track_visibility=True)              