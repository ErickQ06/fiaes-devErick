from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class plan_report(models.Model):   
    _name = 'fiaes.report'
    _inherit= ['mail.thread']
    name=fields.Char("Reporte",compute='compute_name')
    plan_id=fieldsdatetime A combination of a date and a time. Attributes: ()
    meta_id = fields.Many2one(comodel_name='fiaes.meta', string='Meta relacion',track_visibility=True)
    
    codigo = fields.Char(string="Codigo",track_visibility=True)
    fecha_actualizacion = fields.Date(string="Fecha de actualizacion ",track_visibility=True)
    fecha_creacion = fields.Date(string="Fecha de creacion ",track_visibility=True)
    tipo = fields.Selection([('Impacto','Impacto'),('Proceso','Proceso'),('Gestion','Gestion')])
    name = fields.Char(string="Indicador",track_visibility=True)
    desagregaciones = fields.Selection([('Indicador','Tiene sub indicadores'),('Fin','No tiene sub indicadores')],string='Tiene desagregaciones')
    descripcion = fields.Text(string= "Descricion",track_visibility=True)
    uom_id=fields.Many2one("uom.uom",string="Unidad de medida",track_visibility=True)  
    forma_calculo = fields.Text(string="Forma de calculo",track_visibility=True)
    lineabase = fields.Char(string= "Linea base",track_visibility=True)
    frecuencia = fields.Selection([('Mensual','Mensual'),('Trimestral','Trimestral'),('Semestral','Semestral'),('Anual','Anual')],string="Frecuencia de medicion",track_visibility=True)
    fuente = fields.Text(string="Fuente de informacion",track_visibility=True)
    resmedios_id = fields.Many2many(comodel_name='res.users',string="Responsables",track_visibility=True)
    formas = fields.Text(string="Formas de representacion",track_visibility=True)
    usos = fields.Text(string="Usos",track_visibility=True)
    observaciones = fields.Text(string="Observaciones",track_visibility=True)
    valor=fields.Float(string="Valor a conseguir",track_visibility=True)
    meta_id = fields.Many2one(comodel_name='fiaes.meta', string='Meta relacion',track_visibility=True) # relacion con el modelo meta
    objetivo_id = fields.Many2one(comodel_name='fiaes.objetivo',related="meta_id.objetivo_id" ,string="Objetivo relacion",track_visibility=True) # relacion con el objetivo
    pei_id=fields.Many2one(comodel_name='fiaes.pei',string="PEI",related="objetivo_id.pei_id",track_visibility=True) 
    validacion_lines = fields.One2many(comodel_name='fiaes.validacion', inverse_name='indicador_id',track_visibility=True) #list de la validacion
    parent_id=fields.Many2one(comodel_name='fiaes.indicador',string="Indicador padre",track_visibility=True) 
    subindicador_ids = fields.One2many(comodel_name='fiaes.indicador', inverse_name='parent_id',track_visibility=True)
    variable_ids = fields.One2many(comodel_name='fiaes.indicador.variable', inverse_name='indicador_id',track_visibility=True)
    interpretacion_ids = fields.One2many(comodel_name='fiaes.indicador.interpretacion', inverse_name='indicador_id',track_visibility=True)
    calculo=fields.Char('Calculos',compute='compute_meta')
    #objetivo_id = fields.Many2one(comodel_name='fiaes.poaobjetivo', string="Poa objetivos")
    
    @api.one
    @api.depends('parent_id')
    def compute_meta(self):
        for r in self:
            if r.parent_id:
                r.meta_id=r.parent_id.meta_id.id
        
class indicador_variable(models.Model):
    _name='fiaes.indicador.variable'
    _description='variable del indicador'
    name= fields.Char("Variable",track_visibility=True)
    codigo= fields.Char("Nombre corto",track_visibility=True)
    comentario=fields.Text("Descripcion",track_visibility=True)
    indicador_id=fields.Many2one(comodel_name='fiaes.indicador',string="Indicador padre",track_visibility=True)
    
class indicador_interpretacion(models.Model):
    _name='fiaes.indicador.interpretacion'
    _description='variable del indicador'
    name= fields.Char("Interpretacion",track_visibility=True)
    calculo= fields.Char("Condicion",track_visibility=True)
    indicador_id=fields.Many2one(comodel_name='fiaes.indicador',string="Indicador padre",track_visibility=True)
     
    
    
    
#class Peisubindicador(models.Model):
#    _name = 'fiaes.subindicador' 
#    _inherit= ['mail.thread']  
#    codigo = fields.Char(string="Codigo",track_visibility=True)
#    name = fields.Char(string="Indicador",track_visibility=True)
#    uom_id=fields.Many2one("uom.uom",string="Unidad de medida",track_visibility=True)  
#    descripcion = fields.Text(string= "Descricion",track_visibility=True)
#    lineabase = fields.Char(string= "Linea base",track_visibility=True)
#    fechalimite = fields.Date(string="Fecha limite ",track_visibility=True)
#    frecuencia = fields.Selection([('Mensual','Mensual'),('Trimestral','Trimestral'),('Semestral','Semestral'),('Anual','Anual')],string="Frecuencia",track_visibility=True)
#    tipo = fields.Selection([('Impacto','Impacto'),('Proceso','Proceso'),('Gestion','Gestion')])
#    resmedios_id = fields.Many2many(comodel_name='res.users',string="Responsable de los medios de verificacion",track_visibility=True)
#    subindicador_id = fields.Many2one(comodel_name='fiaes.indicador',string="Indicador Relacion",track_visibility=True)


class Peivalidacion(models.Model):
    _name = 'fiaes.validacion'
    _inherit= ['mail.thread'] 
    name = fields.Char(string="Descripcion", track_visibility=True)
    fecha = fields.Date(string="Fecha",track_visibility=True)
    respon = fields.Char(string="Responsable de la medicion",track_visibility=True)
    cantidad = fields.Float(string="Valor",track_visibility=True)
    ubicacion = fields.Char(string="Ubicacion",track_visibility=True)
    territorio = fields.Char(string="Territorio",track_visibility=True)
    indicador_id = fields.Many2one(comodel_name='fiaes.indicador', string="Indicador Relacion",track_visibility=True)
    resmedicion_id = fields.Many2many(comodel_name='res.users',string="Responsable de la medicion",track_visibility=True)
    resvalidacion_id = fields.Many2many(comodel_name='res.users',string="Responsable de la validacion",track_visibility=True)
    state = fields.Selection([('Borrador','Borrador'),('Validado','Validado')],track_visibility=True) 
    respaldo_lines = fields.One2many(comodel_name='fiaes.respaldo', inverse_name='validacion_id',track_visibility=True)


class Peirespaldo(models.Model):
    _name = 'fiaes.respaldo'
    code = fields.Char(string="Codigo")
    name = fields.Char(string="Nombre")
    Descrip = fields.Binary(string="Descripcion del medio ")
    validacion_id = fields.Many2one(comodel_name='fiaes.validacion', string="Validacion")
  

class Peiinr(models.Model):
    _name = 'fiaes.inr'
    _inherit= ['mail.thread']
    actividad = fields.Char(string="Actividad")
    name=fields.Char('Plan de unidad',compute='compute_name')
    descripcion = fields.Text(string="Descripcion")
    proyecto = fields.Many2one(comodel_name='project.project', string="Proyecto")  
    unidad = fields.Many2one(comodel_name='hr.department')
#    objetivo = fields.Many2one(comodel_name='fiaes.objetivo', string="Objetivo")
#    Responsable = fields.Many2many(comodel_name='res.users',string="Responsable")
    lines_id = fields.One2many(comodel_name='fiaes.insumo', inverse_name='inr_id')
#    cantidad = fields.Float(string="Cantidad")
#    preciounitario = fields.Float(string="Precio unitario")
#    monto = fields.Float(string="Monto", compute="monto_total")
#    cuenta = fields.Many2one(comodel_name='account.account',string="Cuenta")
    @api.one
    @api.depends('unidad','proyecto')
    def compute_name(self):
        for r in self:
            if r.proyecto:
                if r.unidad:
                    r.name=r.unidad.name+'('+r.proyecto.name+')'
            else:
                if r.unidad:
                    r.name=r.unidad.name



class Peilineinr(models.Model):
    _name = 'fiaes.inrline'
    recurso = fields.Char(string="Recurso")
    monto = fields.Float(string="Monto")
    mes = fields.Selection([('Enero','Enero'),('Febrero','Febrero'),('Marzo','Marzo'),('Abril','Abril'),('Mayo','Mayo'),('Junio','Junio'),('Julio','Julio'),('Agosto','Agosto'),('Septiembre','Septiembre'),('Octubre','Octubre'),('Noviembre','Noviembre'),('Diciembre','Diciembre')]) 
    cuenta = fields.Char(string='Cuenta')
    inr_id = fields.Many2one(comodel_name='fiaes.inr', string="Inr Relacion")

class Peidnc(models.Model):
    _name = 'fiaes.dnc'     
    _inherit= ['mail.thread'] 
    capacitacion = fields.Char(string="Capacitacion solicitada",track_visibility=True)
    objetivo = fields.Text(string="Objetivo",track_visibility=True)
    Responsable = fields.Many2many(comodel_name='res.users',string="Dirigido a",track_visibility=True)
    proveedor = fields.Char(string="Proveedor",track_visibility=True)
    costo = fields.Float(string="Costo",track_visibility=True)
    participantes = fields.Many2many(comodel_name='res.users',string="Participantes",track_visibility=True)
    mes = fields.Selection([('Enero','Enero'),('Febrero','Febrero'),('Marzo','Marzo'),('Abril','Abril'),('Mayo','Mayo'),('Junio','Junio'),('Julio','Julio'),('Agosto','Agosto'),('Septiembre','Septiembre'),('Octubre','Octubre'),('Noviembre','Noviembre'),('Diciembre','Diciembre')],track_visibility=True)  