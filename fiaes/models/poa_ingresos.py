# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID

#contiene los ingresos de fuentes tradicionales
class poa_ingreso_tradicional(models.Model):
    _name='fiaes.poa.ingreso.tradicional'
    _description='Ingreso de una fuente tradicional por mes'
    name= fields.Char("Fuente")
    poa_id=fields.Many2one(comodel_name='fiaes.poa.ingreso', string='Plan operativo anual',required=True)
    fuente_id=fields.Many2one(comodel_name='fiaes.fuente', string='Fuente de financiamiento',required=True)
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
    utilidad=fields.Float("Utilidad")
    patrimonio=fields.Float("Patrimonio")
    total=fields.Float('Total',compute='sum_total',store=True)
    
    @api.one
    @api.depends('utilidad','patrimonio')
    def sum_total(self):
        for r in self:
            r.total=r.utilidad+r.patrimonio

    @api.constrains('poa_id','fuente_id','mes')
    def check_ingreso(self):
        for r in self:
            existe=self.env['fiaes.poa.ingreso.tradicional'].search(['&',('poa_id','=',r.poa_id.id),('fuente_id','=',r.fuente_id.id),('mes','=',r.mes),('id','!=',r.id)],limit=1)
            if existe:
                raise ValidationError("No  puede repetir el mes y fuente")



#Registra los ingresos por compensacion 
class poa_ingreso_compensacion(models.Model):
    _name='fiaes.poa.ingreso.compensacion'
    _description='Ingreso de compensaciones por mes'
    name= fields.Char("Ingreso por compensacion")
    poa_id=fields.Many2one(comodel_name='fiaes.poa.ingreso', string='Plan operativo anual',required=True)
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
    firmado=fields.Float("Firmado")
    nuevas=fields.Float("Nuevas")
    total=fields.Float('Total',compute='sum_total',store=True)
    firmadocalculado = fields.Float(string="Firmado calculado")
    
    @api.one
    @api.depends('firmado','nuevas')
    def sum_total(self):
        for r in self:
            r.total=r.firmado+r.nuevas

    @api.constrains('poa_id','fuente_id','mes')
    def check_ingreso(self):
        for r in self:
            existe=self.env['fiaes.poa.ingreso.compensacion'].search(['&',('poa_id','=',r.poa_id.id),('mes','=',r.mes),('id','!=',r.id)],limit=1)
            if existe:
                raise ValidationError("No  puede repetir el mes por POA")



#contiene los ingresos de otras fuentes
class poa_ingreso_otros(models.Model):
    _name='fiaes.poa.ingreso.otros'
    _description='Ingreso de otras fuentes de financiamiento'
    name= fields.Char("Fuente")
    poa_id=fields.Many2one(comodel_name='fiaes.poa.ingreso', string='Plan operativo anual',required=True)
    fuente_id=fields.Many2one(comodel_name='fiaes.fuente', string='Fuente de financiamiento',required=True)
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
    monto=fields.Float("Monto")
    supuesto= fields.Char("Supuesto")

    @api.constrains('poa_id','fuente_id','mes')
    def check_ingreso(self):
        for r in self:
            existe=self.env['fiaes.poa.ingreso.tradicional'].search(['&',('poa_id','=',r.poa_id.id),('fuente_id','=',r.fuente_id.id),('mes','=',r.mes),('id','!=',r.id)],limit=1)
            if existe:
                raise ValidationError("No  puede repetir el mes y fuente")



class poa_ingreso(models.Model):
    _name='fiaes.poa.ingreso'
    _inherit= ['mail.thread']
    _description='Ingreso de otras fuentes de financiamiento'
    name=fields.Char("Nombre")
    poa_id=fields.Many2one(comodel_name='fiaes.poa', string='Plan operativo anual',required=True)
    plan_id = fields.Many2one(comodel_name='fiaes.compensacion.desembolso.fase')
    #ingresos
    ingresos_tradicionales=fields.One2many('fiaes.poa.ingreso.tradicional','poa_id', 'Ingresos Tradicionales',track_visibility=True)
    ingresos_tradicionales_supuestos=fields.Text("Supuesto de los ingresos tradicionales",track_visibility=True)
    ingresos_compensaciones=fields.One2many('fiaes.poa.ingreso.compensacion','poa_id', 'Ingresos por compensaciones',track_visibility=True)
    ingresos_compensaciones_supuestos=fields.Text("Supuesto de los ingresos por compensaciones",track_visibility=True)
    ingresos_otros=fields.One2many('fiaes.poa.ingreso.otros','poa_id', 'Ingresos de otras fuentes',track_visibility=True)
    ingresos_otros_supuestos=fields.Text("Supuesto de los otros ingresos",track_visibility=True)
    total_tradicional_utilidad=fields.Float("Total utilidad",compute='sum_tradicional',track_visibility=True)
    total_tradicional_patrimonio=fields.Float("Total Patrimonio",compute='sum_tradicional',track_visibility=True)
    total_tradicional_total=fields.Float("Total",compute='sum_tradicional',track_visibility=True)    
    total_compensacion_firmado=fields.Float("Total firmado",compute='sum_compensacion',track_visibility=True)
    total_compensacion_nuevas=fields.Float("Total nuevas",compute='sum_compensacion',track_visibility=True)
    total_compensacion_total=fields.Float("Total",compute='sum_compensacion',track_visibility=True)
    total_otros=fields.Float("Total",compute='sum_otros',track_visibility=True)
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
                        raise ValidationError("No  puede tener mas de un plan de ingresos aprobado por POA")
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
    @api.depends('ingresos_tradicionales')
    def sum_tradicional(self):
        for r in self:
            totalu=0.0
            totalp=0.0
            totalt=0.0
            for l in r.ingresos_tradicionales:
                totalu=totalu+l.utilidad
                totalp=totalp+l.patrimonio
                totalt=totalt+l.total
            r.total_tradicional_utilidad=totalu
            r.total_tradicional_patrimonio=totalp
            r.total_tradicional_total=totalt
            
            
    @api.one
    @api.depends('ingresos_compensaciones')
    def sum_compensacion(self):
        for r in self:            
            totalf=0.0
            totaln=0.0
            totalt=0.0
            for l in r.ingresos_compensaciones:
                totalf=totalf+l.firmado
                totaln=totaln+l.nuevas
                totalt=totalt+l.total
            r.total_compensacion_firmado=totalf
            r.total_compensacion_nuevas=totaln
            r.total_compensacion_total=totalt
    
    @api.one
    @api.depends('ingresos_otros')
    def sum_otros(self):
        for r in self:            
            total=0.0
            for l in r.ingresos_otros:
                total=total+l.monto
            r.total_otros=total

    @api.one 
    def totalfirmado(self):
        for r in self:
            dict={}
            dict['1'] = 0
            dict['2'] = 0
            dict['3'] = 0
            dict['4'] = 0
            dict['5'] = 0
            dict['6'] = 0
            dict['7'] = 0
            dict['8'] = 0
            dict['9'] = 0
            dict['10'] = 0
            dict['11'] = 0
            dict['12'] = 0
            desembolsos = self.env['fiaes.compensacion.desembolso.desembolso'].search([('fecha', '>=' ,str(r.poa_id.anio)+'-01-01'),('fecha', '<=' ,str(r.poa_id.anio)+'-12-31')])#falta condicion TOD
            for d in desembolsos:
                mes = str(d.fecha.month)
                dict[mes]= dict[mes]+d.monto
            meses={}
            meses['1'] = 'Enero'
            meses['2'] = 'Febrero'
            meses['3'] = 'Marzo'
            meses['4'] = 'Abril'
            meses['5'] = 'Mayo'
            meses['6'] = 'Junio'
            meses['7'] = 'Julio'
            meses['8'] = 'Agosto'
            meses['9'] = 'Septiembre'
            meses['10'] = 'Octubre'
            meses['11'] = 'Noviembre'
            meses['12'] = 'Diciembre'
            for key in dict:
                compensacion = self.env['fiaes.poa.ingreso.compensacion'].search([('poa_id','=',r.id),('mes','=',meses[key])],limit=1)
                if compensacion:
                    compensacion.firmadocalculado = dict[key]
                else:
                    record= {}
                    record['name'] = meses[key]
                    record['poa_id'] = r.id
                    record['mes'] = meses[key]
                    record['firmado'] = 0
                    record['nuevas'] = 0
                    record['firmadocalculado'] = dict[key]
                    compensacion = self.env['fiaes.poa.ingreso.compensacion'].create(record)




 
        
       
