# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID

#contiene los ingresos de fuentes tradicionales
class poa_techo_territorio(models.Model):
    _name='fiaes.poa.techo.territorio'
    _description='Techos presupuestarios por territorio'    
    territorio_id=fields.Many2one(comodel_name='fiaes.territorio', string='Territorio',required=True)
    techo_id=fields.Many2one(comodel_name='fiaes.poa.techo', string='Techo',required=True)
    name=fields.Char("Territorio",related="territorio_id.name")    
    monto=fields.Float("Monto")
    porcentaje_gasto=fields.Float("Porcentaje de gasto",digits=(20,8))
    monto_gasto=fields.Float("Monto de gasto",compute="compute_gasto")
    detalle_ids=fields.One2many('fiaes.poa.techo.territorio.detalle','techo_territorio_id',string='Detalle')
    controlado_total=fields.Float("Gasto/Ingreso",compute="compute_gasto")
    disponible_gastos=fields.Float("Disponible gastos operativos",compute="compute_gasto")
    gasto_operativo=fields.Float("Gasto operativo")
    presupuesto=fields.Float("Presupuesto",compute="compute_gasto")
    diferencia=fields.Float("Diferencia",compute="compute_gasto")
    
    @api.one
    @api.depends('techo_id','porcentaje_gasto','detalle_ids','gasto_operativo')
    def compute_gasto(self):
        for r in self:
            r.monto_gasto=r.monto*r.porcentaje_gasto/100
            total=0.0
            for l in r.detalle_ids:
                if l.suma:
                    total=total-l.monto
                else:
                    total=total+l.monto
            r.controlado_total=total
            r.disponible_gastos=r.monto_gasto-r.controlado_total
            r.presupuesto=r.controlado_total+r.gasto_operativo
            r.diferencia=r.monto_gasto-r.presupuesto
              
    

    @api.constrains('territorio_id','techo_id')
    def check_techo(self):
        for r in self:
            existe=self.env['fiaes.poa.techo.territorio'].search(['&',('territorio_id','=',r.territorio_id.id),('techo_id','=',r.techo_id.id),('id','!=',r.id)],limit=1)
            if existe:
                raise ValidationError("No  puede repetir el territorio")


class poa_techo_territorio_detalle(models.Model):
    _name='fiaes.poa.techo.territorio.detalle'
    _description='Techos presupuestarios por territorio - detalle'  
    name=fields.Char("Decripcion")
    monto=fields.Float("Monto")
    suma=fields.Boolean("Suma al valor")
    techo_territorio_id=fields.Many2one(comodel_name='fiaes.poa.techo.territorio', string='Techo',required=True)
    
    

    tipo=fields.Selection(selection=[('Inversion', 'Total de Inversion')
                                    ,('Ingresos', 'Total de Ingresos')
                                    ,('Compensaciones', 'Total de Compensaciones')
                                    ,('Tradicionales', 'Fuentes tradicionales')
                                    ,('Especifica', 'Fuente especifica')
                                    ,('Monto', 'Monto especifico')]
                                    , string='Tipo',required=True,default='Inversion',track_visibility=True)
    
    
#contiene los ingresos de fuentes tradicionales
class poa_techo_departamento(models.Model):
    _name='fiaes.poa.techo.departamento'
    _description='Techos presupuestarios por departamento'    
    deparment_id=fields.Many2one(comodel_name='hr.department', string='Departamento',required=True)
    techo_id=fields.Many2one(comodel_name='fiaes.poa.techo', string='Techo',required=True)
    name=fields.Char("Departamento",related="deparment_id.name")    
    monto=fields.Float("Monto",compute="compute_gasto")
    monto_ingresado=fields.Float("Monto")
    porcentaje_gasto=fields.Float("Porcentaje de gasto")
    monto_gasto=fields.Float("Monto de gasto",compute="compute_gasto")
    detalle_ids=fields.One2many('fiaes.poa.techo.departamento.detalle','techo_departamento_id',string='Detalle')
    territorio_ids=fields.One2many('fiaes.poa.techo.departamento.territorio','techo_departamento_id',string='Detalle')
    controlado_total=fields.Float("Gastos/Ingresos",compute="compute_gasto")
    disponible_gastos=fields.Float("Disponible gastos operativos",compute="compute_gasto")
    gasto_operativo=fields.Float("Gasto operativo")
    presupuesto=fields.Float("Presupuesto",compute="compute_gasto")
    diferencia=fields.Float("Diferencia",compute="compute_gasto")
    tipo=fields.Selection(selection=[('Inversion', 'Total de Inversion')
                                    ,('Ingresos', 'Total de Ingresos')
                                    ,('Compensaciones', 'Total de Compensaciones')
                                    ,('Tradicionales', 'Fuentes tradicionales')
                                    ,('Especifica', 'Fuente especifica')
                                    ,('Territorio', 'Territorio')
                                    ,('VariosTerritorio', 'Varios Territorios')
                                    ,('Monto', 'Monto especifico')]
                                    , string='Tipo',required=True,default='Inversion',track_visibility=True)
    fuente_id=fields.Many2one(comodel_name='fiaes.fuente', string='Fuente')
    territorio_id=fields.Many2one(comodel_name='fiaes.territorio', string='Territorio')
    supuesto=fields.Text("Supuesto")
    
    @api.one
    @api.depends('techo_id','porcentaje_gasto','detalle_ids','tipo','fuente_id','territorio_id','territorio_ids','monto_ingresado','gasto_operativo')
    def compute_gasto(self):
        for r in self:
            if r.tipo=='Inversion':
                r.monto=r.techo_id.total_territorio
                r.monto_gasto=r.monto*r.porcentaje_gasto/100
            if r.tipo=='Ingresos':
                ingresos=self.env['fiaes.poa.ingreso'].search(['&',('state','=','Aprobado'),('poa_id','=',r.techo_id.poa_id.id)],limit=1)
                r.monto=ingresos.total_tradicional_total+ingresos.total_compensacion_total+ingresos.total_otros
                r.monto_gasto=r.monto*r.porcentaje_gasto/100
            if r.tipo=='Compensaciones':
                ingresos=self.env['fiaes.poa.ingreso'].search(['&',('state','=','Aprobado'),('poa_id','=',r.techo_id.poa_id.id)],limit=1)
                r.monto=ingresos.total_compensacion_total
                r.monto_gasto=r.monto*r.porcentaje_gasto/100
            if r.tipo=='Tradicionales':
                ingresos=self.env['fiaes.poa.ingreso'].search(['&',('state','=','Aprobado'),('poa_id','=',r.techo_id.poa_id.id)],limit=1)
                r.monto=ingresos.total_tradicional_total
                r.monto_gasto=r.monto*r.porcentaje_gasto/100
            if r.tipo=='Especifica':
                fuente=0.0
                ingresos=self.env['fiaes.poa.ingreso'].search(['&',('state','=','Aprobado'),('poa_id','=',r.techo_id.poa_id.id)],limit=1)
                for l in ingresos.ingresos_tradicionales:
                    if l.fuente_id.id==r.fuente_id.id:
                        fuente=fuente+l.total
                for l in ingresos.ingresos_otros:
                    if l.fuente_id.id==r.fuente_id.id:
                        fuente=fuente+l.monto
                r.monto=fuente;
                r.monto_gasto=r.monto*r.porcentaje_gasto/100
            if r.tipo=='Territorio':
                territorio=0.0
                for l in r.techo_id.techo_territorio_ids:
                    if l.territorio_id.id==r.territorio_id.id:
                        territorio=l.gasto_operativo
                r.monto=territorio
                r.monto_gasto=r.monto*r.porcentaje_gasto/100
            if r.tipo=='VariosTerritorio':
                territorio=0.0
                for l in r.territorio_ids:
                    territorio=territorio+l.monto
                r.monto=territorio
                r.monto_gasto=territorio
            if r.tipo=='Monto':
                r.monto=r.monto_ingresado
                r.monto_gasto=r.monto
                
            total=0.0
            for l in r.detalle_ids:
                if l.suma:
                    total=total-l.monto
                else:
                    total=total+l.monto
            r.controlado_total=total
            r.disponible_gastos=r.monto_gasto-r.controlado_total
            r.presupuesto=r.controlado_total+r.gasto_operativo
            r.diferencia=r.monto_gasto-r.presupuesto
              
    

    @api.constrains('deparment_id','techo_id')
    def check_techo(self):
        for r in self:
            existe=self.env['fiaes.poa.techo.departamento'].search(['&',('deparment_id','=',r.territorio_id.id),('techo_id','=',r.techo_id.id),('id','!=',r.id)],limit=1)
            if existe:
                raise ValidationError("No  puede repetir el departamento")    


class poa_techo_departamento_detalle(models.Model):
    _name='fiaes.poa.techo.departamento.territorio'
    _description='Montos por territorio'  
    name=fields.Char("Decripcion",related='territorio_id.name')
    base=fields.Float("Base",compute='_get_monto')
    territorio_id=fields.Many2one(comodel_name='fiaes.territorio', string='Territorio')
    porcentaje=fields.Float("Porcentaje")
    monto=fields.Float("Monto",compute='_calculate_monto')
    techo_departamento_id=fields.Many2one(comodel_name='fiaes.poa.techo.departamento', string='Techo',required=True)
    
    @api.one
    @api.depends('territorio_id')
    def _get_monto(self):
        for r in self:
            territorio=0.0
            for l in r.techo_departamento_id.techo_id.techo_territorio_ids:
                if l.territorio_id.id==r.territorio_id.id:
                    territorio=l.gasto_operativo
            r.base=territorio
    
    @api.one
    @api.depends('territorio_id','porcentaje')
    def _calculate_monto(self):
        for r in self:
            r.monto=r.base*r.porcentaje/100.00

class poa_techo_departamento_detalle(models.Model):
    _name='fiaes.poa.techo.departamento.detalle'
    _description='Techos presupuestarios por departamento - detalle'  
    name=fields.Char("Decripcion")
    monto=fields.Float("Monto")
    suma=fields.Boolean("Suma al valor")
    techo_departamento_id=fields.Many2one(comodel_name='fiaes.poa.techo.departamento', string='Techo',required=True)


class poa_techo(models.Model):
    _name='fiaes.poa.techo'
    _inherit= ['mail.thread']
    _description='Techos presupuestarios'
    name=fields.Char("Nombre")
    poa_id=fields.Many2one(comodel_name='fiaes.poa', string='Plan operativo anual',required=True)
     #ingresos
    techo_territorio_ids=fields.One2many('fiaes.poa.techo.territorio','techo_id', 'Techos por territorio',track_visibility=True)
    techo_territorio_supuestos=fields.Text("Supuesto de los techos territoriales",track_visibility=True)        
    total_territorio=fields.Float("Total inversion territorios",compute='sum_territorio',track_visibility=True)
    
    techo_departamento_ids=fields.One2many('fiaes.poa.techo.departamento','techo_id', 'Techos por departamento',track_visibility=True)
    techo_departamento_supuestos=fields.Text("Supuesto de los techos por departamento",track_visibility=True)        
    total_departamento=fields.Float("Total de gastos por departamento",compute='sum_departamento',track_visibility=True)
    
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado',required=True,default='Borrador',track_visibility=True)
    
    @api.one
    def aprobar(self):
        for r in self:
            for l in r.poa_id.ingresos:
                if l.state=='Aprobado':
                    if l.id!=r.id:
                        raise ValidationError("No  puede tener mas de un plan de techos aprobado por POA")
            r.state='Aprobado'
    
    
    @api.one
    def regresar(self):
        for r in self:
            r.state='Borrador'
    
    @api.one
    def cancelar(self):
        for r in self:
            r.state='Cancelado'
                
    @api.one
    @api.depends('techo_territorio_ids')
    def sum_territorio(self):
        for r in self:
            totalt=0.0
            for l in r.techo_territorio_ids:
                totalt=totalt+l.monto
            r.total_territorio=totalt
    
    @api.one
    @api.depends('techo_departamento_ids')
    def sum_departamento(self):
        for r in self:
            totalt=0.0
            for l in r.techo_departamento_ids:
                totalt=totalt+l.monto
            r.total_departamento=totalt