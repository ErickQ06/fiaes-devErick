# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class compensacion(models.Model):
    _inherit='sale.order'
    nombre_comercial=fields.Char("Nombre comercial",related='partner_id.nombre_comercial',store='fase')
    nit=fields.Char("NIT",related='partner_id.nit',store='fase')
    representante_nombre=fields.Char("Representante legal",related='partner_id.representante_nombre',store='fase')
    representante_nit=fields.Char("NIT del representante",related='partner_id.representante_nit',store='fase')
    representante_dui=fields.Char("NRC del representante",related='partner_id.representante_dui',store='fase')
    representante_nacionalidad=fields.Many2one(comodel_name='res.country', string='Nacionalidad del representante',related='partner_id.representante_nacionalidad',store='fase')
    representante_nacimiento=fields.Date("Fecha de nacimiento del representante legal",related='partner_id.representante_nacimiento',store='fase')
    representante_profesion=fields.Char("Profesion del representante legal",related='partner_id.representante_profesion',store='fase')
    departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento',related='partner_id.departamento_id',store='fase')
    municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio',related='partner_id.municipio_id',store='fase')
    poryecto_ambiental=fields.Char("Nombre del proyecto de compensacion ambiental")
    resolucion_marn=fields.Char("Numero de resolucion del MARN")
    resolucion_fecha=fields.Date("Fecha de resolucion del MARN")
    proyecto_direcion=fields.Char("Direccion del proyecto de compensacion ambiental")
    proyecto_departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento del proyecto de compensacion ambiental')
    proyecto_municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio del proyecto de compensacion ambiental')
    descripcion=fields.Text("Descripcion de la afectacion de la compensacion ambiental")
    rubro=fields.Char("Rubro de afectacion de la compensacion ambiental")
    area=fields.Char("Area strategica del FIAES a trabajar")
    valor=fields.Float("Valor del convenio")
    desembolsos=fields.Float("Numero de desembolsos")
    fianza=fields.Float("Monto de fianza de fiel cumplimento")


#Proyecto institucional
class proyecto_institucional(models.Model):
    _inherit='project.project'
    codigo=fields.Char("Codigo")
    tipo=fields.Selection(selection=[('Institucional', 'Proyecto Institucional')
                                        ,('Administrado', 'Administrado')]
                                        , string='Tipo de Proyecto',default='Institucional')
    fuente_ids=fields.Many2many(comodel_name='fiaes.fuente', relation='proyecto_fuente_rel',string='Fuentes')
    contacto_ids=fields.Many2many(comodel_name='res.partner', relation='proyecto_contacto_rel', string='Contactos')
    responsable_ids=fields.Many2many(comodel_name='res.partner', relation='proyecto_responsable_rel', string='Responsable')
    cordenada_ids=fields.One2many('fiaes.proyecto_cordenadas','proyecto_id', 'Cordenadas')
    objetivo_ids=fields.One2many('fiaes.proyecto_objetivo','proyecto_id', 'Objetivos especificos')
    territorio_ids=fields.Many2many(comodel_name='fiaes.territorio', string='Territorio')
    objetivo=fields.Text("Objetivo General")


class proyecto_objetivo(models.Model):
    _name = "fiaes.proyecto_objetivo"
    _description = "Objetivos especificos"
    name = fields.Char('Obetivo')
    proyecto_id=fields.Many2one(comodel_name='project.project', string='Proyecto')


class proyecto_cordenadas(models.Model):
    _name = "fiaes.proyecto_cordenadas"
    _description = "Cordenadas donde se desarrolla el proyecto"
    name = fields.Char('Descripcion')
    coordenadas_latitud=fields.Float("Latitud",digits=(20,7))
    coordenadas_longitud=fields.Float("Longitud",digits=(20,7))
    proyecto_id=fields.Many2one(comodel_name='project.project', string='Proyecto')

class task_institucional(models.Model):
    _inherit='project.task'
    codigo=fields.Char("Codigo")
    objetivo_id=fields.Many2one(comodel_name='fiaes.proyecto_objetivo', string='Objetivo')
    tipo=fields.Selection(selection=[('Institucional', 'Proyecto Institucional')
                                        ,('Administrado', 'Administrado')]
                                        , string='Tipo de Proyecto',related="project_id.tipo")
    responsable_ids=fields.Many2many(comodel_name='res.partner', relation='task_responsable_rel', string='Responsables')
    cordinacion_ids=fields.Many2many(comodel_name='res.partner', relation='task_cordinacion_rel', string='En coordinacion')
    inicio=fields.Date("Fecha de inicio")
    fin=fields.Date("Fecha de fin")
    territorio_ids=fields.Many2many(comodel_name='fiaes.territorio', string='Territorio')
    cordenada_ids=fields.One2many('fiaes.task_cordenadas','task_id', 'Cordenadas')
    recurso_ids=fields.One2many('fiaes.task_recurso','task_id', 'Recursos')
    recurso_child_ids=fields.One2many('fiaes.task_recurso','parent_task_id', 'Recursos')
    has_childs=fields.Boolean('Has childs',compute='compute_child',store='False')

    @api.one
    @api.depends('child_ids')
    def compute_child(self):
        for record in self:
            if record.child_ids:
                record.has_childs=True
            else:
                record.has_childs=False

class task_cordenadas(models.Model):
    _name = "fiaes.task_cordenadas"
    _description = "Cordenadas donde se desarrolla el proyecto"
    name = fields.Char('Descripcion')
    coordenadas_latitud=fields.Float("Latitud",digits=(20,7))
    coordenadas_longitud=fields.Float("Longitud",digits=(20,7))
    task_id=fields.Many2one(comodel_name='project.task', string='Actividad')

class task_recursos(models.Model):
    _name = "fiaes.task_recurso"
    _description = "Recursos institucionales"
    name = fields.Char('Nombre')
    cantidad=fields.Float("Cantidad",digits=(20,3))
    descripcion = fields.Char('Descripcion')
    account_id=fields.Many2one(comodel_name='account.account', string='Cuenta asociada')
    valor=fields.Float("Valor estimado",digits=(20,3))
    task_id=fields.Many2one(comodel_name='project.task', string='Actividad')
    parent_task_id=fields.Many2one(comodel_name='project.task', related='task_id.parent_id', string='Actividad padre')
    tipo=fields.Selection(selection=[('Institucional', 'Proyecto Institucional')
                                        ,('Administrado', 'Administrado')]
                                        , string='Tipo de Proyecto',related="task_id.tipo")



class proyecto(models.Model):
    _name = "fiaes.proyecto"
    _description='Proyecto Compensacion'
    name=fields.Char("Proyecto")
    fuentes_ids=fields.Many2many('fiaes.fuente')
    codigo=fields.Char("Codigo")
    departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento')
    municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio')
    coordenadas_latitud=fields.Float("Latitud",digits=(20,7))
    coordenadas_longitud=fields.Float("Longitud",digits=(20,7))
    afectacion=fields.Text("Tipo de afectacion")
    ejecutora=fields.Many2one(comodel_name='res.partner', string='Ejecutora')
    contrapartida=fields.Float("Contrapartida")
    aliados=fields.Many2many('res.partner','Aliados')
    estado=fields.Selection(selection=[('Estado1', 'Estado1')
                                        ,('Estado2', 'Estado2')]
                                        , string='Estado')
