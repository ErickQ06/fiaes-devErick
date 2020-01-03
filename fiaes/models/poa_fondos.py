# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class inversion(models.Model):
    _name='fiaes.inversion'
    _inherit= ['mail.thread']
    _description='Invesion en territorio'
    name= fields.Char("Componente",track_visibility=True)
    uet_id=fields.Many2one("fiaes.uet",string="UET",track_visibility=True)
    conservacion_id=fields.Many2one("fiaes.conservacion",string="Objeto de Conservacion",track_visibility=True)
    territorio_id=fields.Many2one("fiaes.territorio",string="Territorio",track_visibility=True)
    poa_id=fields.Many2one(comodel_name='fiaes.poa', string='Plan operativo anual',required=True)
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Presentado', 'Presentado')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado',required=True,default='Borrador',track_visibility=True)
    actividad_ids=fields.One2many('fiaes.inversion.actividad','inversion_id',string='Actividades')
    indicador_ids=fields.One2many('fiaes.inversion.indicador','inversion_id',string='Indicadores')
    desembolso_ids=fields.One2many('fiaes.inversion.actividad.desembolso','inversion_id',string='Desembolsos')
    total_disponible=fields.Float("Total disponible",compute='calcular_disponible',store=False)
    total_programado=fields.Float("Total programado",compute='calcular_disponible',store=False)
    convocatoria_id=fields.Many2one("fiaes.convocatoria",string="Convocatoria",track_visibility=True)
    
    
    @api.one
    @api.depends('poa_id','actividad_ids')
    def calcular_disponible(self):
        for r in self:            
            total=0.0
            presupuesto_total=0.0
            inversiones = self.env['fiaes.inversion'].search(['&',('territorio_id','=',r.territorio_id.id),('poa_id','=',r.poa_id.id)])
            for l in inversiones:
                for ld in l.actividad_ids:
                    total=total+ld.total_insumos
                for le in l.desembolso_ids:
                    total=total+le.total
            presupuesto=self.env['fiaes.poa.techo'].search(['&',('state','=','Aprobado'),('poa_id','=',r.poa_id.id)],limit=1)
            if presupuesto:
                for l in presupuesto.techo_territorio_ids:
                    if l.territorio_id.id==r.territorio_id.id:
                        presupuesto_total=l.monto            
            r.total_disponible=presupuesto_total-total
            totalprogramado=0.0
            for a in r.actividad_ids:
                totalprogramado=totalprogramado+a.total_insumos
            for d in r.desembolso_ids:
                totalprogramado=totalprogramado+d.total
            r.total_programado=totalprogramado
    
    @api.one
    def aprobar(self):
        for r in self:
            proyecto=self.env['project.project'].create({'name':r.name})
            for a in r.actividad_ids:
                task=self.env['project.task'].create({'project_id':proyecto.id,'name':a.name})
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
            



class inversion_actividad_desembolso(models.Model):
    _name='fiaes.inversion.actividad.desembolso'
    _description='Invesion en territorio - Desembolsos por actividad'
    name=fields.Char("Descripcion",track_visibility=True)
    total=fields.Float("Desembolso" )
    inversion_id=fields.Many2one("fiaes.inversion",string="inversion",track_visibility=True)
    convocatoria_id=fields.Many2one("fiaes.convocatoria",string="Convocatoria",track_visibility=True)
    mes=fields.Selection(selection=[('Enero', 'Enero')
                                    ,('Febrero', 'Febrero')
                                    ,('Marzo', 'Marzo')
                                    ,('Abril', 'Abril')
                                    ,('Mayo', 'Mayo')
                                    ,('Junio', 'Junio')
                                    ,('Julio', 'Julio')
                                    ,('Agosto', 'Agosto')
                                    ,('Septiembre', 'Septiembre')
                                    ,('Octubre', 'Octubre')
                                    ,('Noviembre', 'Noviembre')
                                    ,('Diciembre', 'Diciembre')]
                                    , string='Mes',required=True)
    anio=fields.Char(string='Año',required=True)
    fuente_id=fields.Many2one("fiaes.fuente",string="Fuente de financiamiento",track_visibility=True)
    uet_id=fields.Many2one("fiaes.uet",string="UET",related="inversion_id.uet_id",track_visibility=True,store=True)
    conservacion_id=fields.Many2one("fiaes.conservacion",related='inversion_id.conservacion_id',string="Objeto de Cons.",track_visibility=True,store=True)
    territorio_id=fields.Many2one("fiaes.territorio",string="Territorio",related="inversion_id.territorio_id",track_visibility=True,store=True)
    poa_id=fields.Many2one(comodel_name='fiaes.poa', string='Plan operativo anual',related="inversion_id.poa_id",store=True)
    state_inversion=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado del componente',related="inversion_id.state",default='Borrador',track_visibility=True,store=True)
    state_convocatoria=fields.Selection(selection=[('Nueva', 'Nueva')
                                    ,('A Licitar', 'A Licitar')
                                    ,('Comprometida', 'Comprometida')
                                    ,('Finalizada', 'Finalizada')]
                                    , string='Estado',related="convocatoria_id.state",default='Nueva',track_visibility=True,store=True)

    




class inversion_actividad(models.Model):
    _name='fiaes.inversion.actividad'
    _inherit= ['mail.thread']
    _description='Actividades de Invesion en territorio'
    name= fields.Char("Actividad",track_visibility=True)
    resultado=fields.Char("Resultado descripcion",track_visibility=True)
    cantidad=fields.Char("Resultado cantidad",track_visibility=True)
    conservacion_id=fields.Many2one("fiaes.conservacion",related='inversion_id.conservacion_id',string="Objeto de Conservacion",track_visibility=True,store=True)
    producto_id=fields.Many2one("fiaes.producto",string="Producto",track_visibility=True)
    convocatoria_id=fields.Many2one("fiaes.convocatoria",related='inversion_id.convocatoria_id',string="Convocatoria",track_visibility=True,store=True)
    inversion_id=fields.Many2one("fiaes.inversion",string="inversion",track_visibility=True)
    insumo_ids=fields.One2many('fiaes.inversion.actividad.insumo','inversion_actividad_id',string='Insumos')
    resultado_ids=fields.One2many('fiaes.inversion.actividad.resultado','inversion_actividad_id',string='Resultados')
    total_insumos=fields.Float("Total insumos",compute='sum_otros',track_visibility=True)
    uet_id=fields.Many2one("fiaes.uet",string="UET",related="inversion_id.uet_id",track_visibility=True,store=True)
    prioridad=fields.Integer("Prioridad")
    state_inversion=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado de la inversion',related="inversion_id.state",required=True,default='Borrador',track_visibility=True,store=True)
    #total_desembolsos=fields.Float("Total desembolsos",compute='sum_otros',track_visibility=True)
    
     
    @api.one
    @api.depends('insumo_ids')
    def sum_otros(self):
        for r in self:            
            total=0.0
            for l in r.insumo_ids:
                total=total+l.total
            r.total_insumos=total

    
class inversion_actividad_insumo(models.Model):
    _name='fiaes.inversion.actividad.insumo'
    _description='Componente - Insumos por producto'
    name=fields.Char("Insumo",track_visibility=True)
    tecnica_id=fields.Many2one("fiaes.tecnica",string="Tecnica de restauracion",track_visibility=True)
    uom_id=fields.Many2one("uom.uom",string="Unidad de medida",track_visibility=True)
    cantidad=fields.Float("Cantidad")
    costo_unitario=fields.Float("Costo unitario")
    total=fields.Float("Total",compute='calculate_total',store=True )
    inversion_actividad_id=fields.Many2one("fiaes.inversion.actividad",string="Actividad",track_visibility=True)
    mes=fields.Selection(selection=[('Enero', 'Enero')
                                    ,('Febrero', 'Febrero')
                                    ,('Marzo', 'Marzo')
                                    ,('Abril', 'Abril')
                                    ,('Mayo', 'Mayo')
                                    ,('Junio', 'Junio')
                                    ,('Julio', 'Julio')
                                    ,('Agosto', 'Agosto')
                                    ,('Septiembre', 'Septiembre')
                                    ,('Octubre', 'Octubre')
                                    ,('Noviembre', 'Noviembre')
                                    ,('Diciembre', 'Diciembre')]
                                    , string='Mes',required=True)
    anio1=fields.Char(string='year')
    fuente_id=fields.Many2one("fiaes.fuente",string="Fuente de financiamiento",track_visibility=True)
    inversion_id=fields.Many2one("fiaes.inversion",related="inversion_actividad_id.inversion_id",string="Componente",track_visibility=True,store=True)
    uet_id=fields.Many2one("fiaes.uet",string="UET",related="inversion_id.uet_id",track_visibility=True,store=True)
    producto_id=fields.Many2one("fiaes.producto",string="Producto",related="inversion_actividad_id.producto_id",track_visibility=True,store=True)
    conservacion_id=fields.Many2one("fiaes.conservacion",related='producto_id.conservacion_id',string="Objeto de Cons.",track_visibility=True,store=True)
    territorio_id=fields.Many2one("fiaes.territorio",string="Territorio",related="inversion_id.territorio_id",track_visibility=True,store=True)
    poa_id=fields.Many2one(comodel_name='fiaes.poa', string='Plan operativo anual',related="inversion_id.poa_id",store=True)
    state_inversion=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado del componente',related="inversion_id.state",default='Borrador',track_visibility=True,store=True)
    convocatoria_id=fields.Many2one("fiaes.convocatoria",string="Convocatoria",related="inversion_actividad_id.convocatoria_id",track_visibility=True,store=True)
    state_convocatoria=fields.Selection(selection=[('Nueva', 'Nueva')
                                    ,('A Licitar', 'A Licitar')
                                    ,('Comprometida', 'Comprometida')
                                    ,('Finalizada', 'Finalizada')]
                                    , string='Estado',related="convocatoria_id.state",default='Nueva',track_visibility=True,store=True)
    prioridad=fields.Integer("Prioridad",related="inversion_actividad_id.prioridad",store=True)

    @api.one
    @api.depends('cantidad','costo_unitario')
    def calculate_total(self):
        for r in self:                        
            r.total=r.cantidad*r.costo_unitario
    
    @api.one
    def duplicate(self):
        for r in self:
            dic={}
            dic['name']=r.name
            dic['tecnica_id']=r.tecnica_id.id
            dic['inversion_actividad_id']=r.inversion_actividad_id.id
            dic['costo_unitario']=r.costo_unitario
            dic['cantidad']=r.cantidad
            dic['mes']=r.mes
            dic['anio1']=r.anio1
            dic['fuente_id']=r.fuente_id.id
            dic['uom_id']=r.uom_id.id
            self.env['fiaes.inversion.actividad.insumo'].create(dic)

class resultado(models.Model):
    _name = 'fiaes.inversion.actividad.resultado'
    _description='Resultados de la actividad'
    _inherit = ['mail.thread']
    name = fields.Char(string="Resultado")
    uom_id=fields.Many2one("uom.uom",string="Unidad de medida",track_visibility=True)  
    inversion_actividad_id=fields.Many2one("fiaes.inversion.actividad",string="Actividad",track_visibility=True)
    cantidad = fields.Float(string="Meta")
    supuesto = fields.Char(string="Supuesto")
    inversion_id=fields.Many2one("fiaes.inversion",related="inversion_actividad_id.inversion_id",string="Componente",track_visibility=True,store=True)
    uet_id=fields.Many2one("fiaes.uet",string="UET",related="inversion_id.uet_id",track_visibility=True,store=True)
    producto_id=fields.Many2one("fiaes.producto",string="Producto",related="inversion_actividad_id.producto_id",track_visibility=True,store=True)
    conservacion_id=fields.Many2one("fiaes.conservacion",related='producto_id.conservacion_id',string="Objeto de Cons.",track_visibility=True,store=True)
    territorio_id=fields.Many2one("fiaes.territorio",string="Territorio",related="inversion_id.territorio_id",track_visibility=True,store=True)
    poa_id=fields.Many2one(comodel_name='fiaes.poa', string='Plan operativo anual',related="inversion_id.poa_id",store=True)
    state_inversion=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado del componente',related="inversion_id.state",default='Borrador',track_visibility=True,store=True)
    convocatoria_id=fields.Many2one("fiaes.convocatoria",string="Convocatoria",related="inversion_actividad_id.convocatoria_id",track_visibility=True,store=True)
    state_convocatoria=fields.Selection(selection=[('Nueva', 'Nueva')
                                    ,('A Licitar', 'A Licitar')
                                    ,('Comprometida', 'Comprometida')
                                    ,('Finalizada', 'Finalizada')]
                                    , string='Estado',related="convocatoria_id.state",default='Nueva',track_visibility=True,store=True)
    prioridad=fields.Integer("Prioridad",related="inversion_actividad_id.prioridad",store=True)


    
class inversion_indicador(models.Model):
    _name='fiaes.inversion.indicador'
    _description='Indicadores del PEI involucrados en la Invesion en territorio'
    inversion_id=fields.Many2one("fiaes.inversion",string="Inversion",track_visibility=True)
    indicador_id=fields.Many2one("fiaes.indicador",string="Indicador",track_visibility=True)
    name= fields.Char("Indicador", related="indicador_id.name",track_visibility=True,store=True)
    uom_id=fields.Many2one("uom.uom",related='indicador_id.uom_id',string="Unidad de medida",track_visibility=True,store=True)
    frecuencia = fields.Selection([('Mensual','Mensual'),('Trimestral','Trimestral'),('Semestral','Semestral'),('Anual','Anual')],related='indicador_id.frecuencia',string="Frecuencia",store=True)
    cantidad=fields.Float("meta",track_visibility=True)
    

class inversion_actividad_insumo(models.Model):
    _name='fiaes.inversion.reporte'
    _auto=False
    _description='Componente - Insumos por producto'
    name=fields.Char("Descripcion")
    tipo=fields.Char("Tipo")
    total=fields.Float("Desembolso" )
    inversion_id=fields.Many2one("fiaes.inversion",string="inversion")
    convocatoria_id=fields.Many2one("fiaes.convocatoria",string="Convocatoria")
    mes=fields.Selection(selection=[('Enero', 'Enero')
                                    ,('Febrero', 'Febrero')
                                    ,('Marzo', 'Marzo')
                                    ,('Abril', 'Abril')
                                    ,('Mayo', 'Mayo')
                                    ,('Junio', 'Junio')
                                    ,('Julio', 'Julio')
                                    ,('Agosto', 'Agosto')
                                    ,('Septiembre', 'Septiembre')
                                    ,('Octubre', 'Octubre')
                                    ,('Noviembre', 'Noviembre')
                                    ,('Diciembre', 'Diciembre')]
                                    , string='Mes',required=True)
    anio=fields.Char(string='Año')
    fuente_id=fields.Many2one("fiaes.fuente",string="Fuente de financiamiento")
    uet_id=fields.Many2one("fiaes.uet",string="UET")
    conservacion_id=fields.Many2one("fiaes.conservacion",string="Objeto de Cons.")
    territorio_id=fields.Many2one("fiaes.territorio",string="Territorio")
    poa_id=fields.Many2one(comodel_name='fiaes.poa', string='Plan operativo anual')
    
    @api.model_cr  # cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""CREATE OR REPLACE VIEW %s AS
                         (select 10000000+iad.id as id,'Desembolso' as tipo,iad."name",iad.total,iad.inversion_id,iad.convocatoria_id,iad.mes,iad.anio,iad.fuente_id,iad.uet_id,iad.conservacion_id,iad.territorio_id,iad.poa_id
                            from fiaes_inversion_actividad_desembolso iad
                            union all
                            select 20000000+iad.id as id,'Insumo' as tipo,iad."name",iad.total,iad.inversion_id,iad.convocatoria_id,iad.mes,iad.anio1 as anio,iad.fuente_id,iad.uet_id,iad.conservacion_id,iad.territorio_id,iad.poa_id
                            from fiaes_inversion_actividad_insumo iad
                         )"""% self._table)
    