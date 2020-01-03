# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class compensacion_afectacion(models.Model):
    _name='fiaes.compensacion.afectacion'
    _inherit= ['mail.thread']
    _description= 'Afectacion'
    name=fields.Char("Afectacion")
    descripcion=fields.Text("Descripcion")
    uom_id=fields.Many2one("uom.uom",string="Unidad de medida",track_visibility=True)


class solicitud_proyecto(models.Model):
    _name='fiaes.compensacion.proyecto'
    _inherit= ['mail.thread']
    _description= 'Registro de proyectos'
    name=fields.Char("Proyecto")
    descripcion=fields.Text("Descripcion")
    resolucion=fields.Char("Numero de resolucion")
    resolucion_NFA=fields.Char("Numero de resolucion NFA")
    resolucion_fecha=fields.Date("Fecha de resolucion")
    direccion=fields.Char("Direccion del proyecto")
    departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento donde esta la empresa')
    municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio donde esta la empresa')
    afectacion=fields.Text("Descripción de la afectación del proyecto")
    vencimiento=fields.Date("Vencimiento de la resolucion")
    valor=fields.Float("Valor de la resolucion")
    state=fields.Selection(selection=[('Solicitado', 'Solicitado')
                                    ,('Evaluando', 'Evaluando')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Rechazado', 'Rechazado')]
                                    , string='Estado',required=True,default='Solicitado',track_visibility=True)
    titular_id=fields.Many2one(comodel_name='res.partner', string='Titular')
    afectacion_ids=fields.One2many('fiaes.compensacion.proyecto.afectacion','proyecto_id',string='Afectaciones')
    porcentaje_admon=fields.Float("Porcentaje de administracion")
    
    total_deuda_lp=fields.Float("Total de deuda a largo plazo",compute='calcular',store=False)
    total_deuda_cp=fields.Float("Total de deuda a corto plazo",compute='calcular',store=False)
    total_pagado=fields.Float("Suma de pagos efectuados",compute='calcular',store=False)
    disponible_sin_gastos=fields.Float("Disponible sin gastos administrativos aplicados")
    disponible_con_gastos=fields.Float("Disponible con gastos administrativos aplicados")
    gasto_operativo=fields.Float("Gasto operativo",compute='calcular',store=False)
    gasto_administrativo=fields.Float("Gasto administrativo",compute='calcular',store=False)
    financiamineto_proyectos=fields.Float("Financiacion a proyectos",compute='calcular',store=False)
    coordenadas_latitud=fields.Float("Latitud",digits=(20,7))
    coordenadas_longitud=fields.Float("Longitud",digits=(20,7))
    
    
    @api.one
    def calcular(self):
        for r in self:
            lp=0.0
            cp=0.0
            desembolsos=self.env['fiaes.compensacion.desembolso.desembolso'].search([('projecto_id','=',r.id)])
            for d in desembolsos:
                if d.corto_move_id:
                    cp=cp+d.monto
                else:
                    if d.largo_move_id:
                        lp=lp+d.monto
            p=0.0
            pagos=self.env['account.payment'].search([('partner_id','=',r.titular_id.id)])
            for pago in pagos:
                p=p+pago.amount
            ga=0.0
            go=0.0
            iv=0.0
            gastos=self.env['fiaes.compensacion.pack.proyecto.desembolso'].search([('projecto_compensacion_id','=',r.id)])
            for gasto in gastos:
                ga=ga+gasto.monto_administrativo
                go=go+gasto.monto_operativo
                iv=iv+gasto.monto_ejecutora
            r.total_deuda_lp=lp
            r.total_deuda_cp=cp
            r.total_pagado=p
            r.gasto_administrativo=ga
            r.gasto_operativo=go
            r.financiamineto_proyectos=iv
            
    
    @api.one
    def contactar(self):
        for r in self:
            r.state='Evaluando'
    
    @api.one
    def aprobar(self):
        for r in self:
            r.state='Aprobado'
            #enviando el correo de confirmacion
            template = self.env.ref('fiaes.compensacion_proyecto_aprobado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)

    
    @api.one
    def rechazar(self):
        for r in self:
            r.state='Rechazado'
            #enviando el correo de confirmacion
            template = self.env.ref('fiaes.compensacion_proyecto_rechazo', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)

class compensacion_proyecto_afectacion(models.Model):
    _name='fiaes.compensacion.proyecto.afectacion'
    _description= 'Afectacion'
    name=fields.Char("Descripcion")
    uom_id=fields.Many2one("uom.uom",related='afectacion_id.uom_id',string="Unidad de medida",track_visibility=True)
    afectacion_id=fields.Many2one("fiaes.compensacion.afectacion",string="Afectacion",track_visibility=True)
    proyecto_id=fields.Many2one("fiaes.compensacion.proyecto",string="proyecto",track_visibility=True)
    cantidad=fields.Float("Medida de la afectacion")
    cantidad_ha=fields.Float("Area equivalente")
    conservacion_ids=fields.Many2many(comodel_name='fiaes.conservacion', string='Objetos de conservacion')
    
    
    
    
class compensacion_proyecto_fianza(models.Model):
    _name='fiaes.compensacion.fianza'
    _inherit= ['mail.thread']
    _description= 'Fianza'
    name=fields.Char("Fianza")
    proyecto_id=fields.Many2one("fiaes.compensacion.proyecto",string="proyecto",track_visibility=True)
    titular_id=fields.Many2one(comodel_name='res.partner', related='proyecto_id.titular_id', string='Titular')
    aseguradora=fields.Char("Aseguradora")
    monto=fields.Float("Monto")
    fecha_emision=fields.Date("Fecha")
    fecha_vencimiento=fields.Date("Fecha de vencimiento")
    fianza=fields.Binary("Poder General Administrativo o equivalente")
    fianza_filename=fields.Char("Poder file name")
    
    @api.model
    def create(self, values):
        # Override the original create function for the res.partner model
        record = super(compensacion_proyecto_fianza, self).create(values)
        #enviando el correo de confirmacion
        #creando las alertas
        alertdate=record.fecha+relativedelta(months=-1)
        self.env['fiaes.compensacion.fianza.alerta'].create({'desembolso_id':record.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
        alertdate=record.fecha+relativedelta(days=-7)
        self.env['fiaes.compensacion.fianza.alerta'].create({'desembolso_id':record.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
        return record
    
    

class proyectoplanalertas_fainza(models.Model):
    _name='fiaes.compensacion.fianza.alerta'
    name = fields.Char()
    fianza_id = fields.Many2one(comodel_name='fiaes.compensacion.fianza')
    projecto_id = fields.Many2one(comodel_name='fiaes.compensacion.proyecto',string="Proyecto", related='fianza_id.proyecto_id')
    titular_id=fields.Many2one(comodel_name='res.partner', string='Titular',related='projecto_id.titular_id')
    usuario_id=fields.Many2one(comodel_name='res.users', string='Usuario asociado',related='titular_id.usuario_id')
    employee_id=fields.Many2one(comodel_name='hr.employee', string='Enlace',related='titular_id.employee_id')
    fecha=fields.Date(string="Fecha")
    ejecutado=fields.Boolean("Ejecutado")
    
    
    @api.one
    def callall(self):
        hoy=date.today()
        alertas=self.env['fiaes.compensacion.fianza.alerta'].search([('fecha','<=',datetime.strftime(hoy, '%Y-%m-%d')),('ejecutado','=',False)])
        template = self.env.ref('fiaes.compensacion_fianza_alerta', False)
        for alerta in alertas:
            if template:
                self.env['mail.template'].browse(template.id).send_mail(alerta.id)