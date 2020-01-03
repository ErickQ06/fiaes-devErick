# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID

class Cuentascompensacion(models.Model):
    _inherit = 'res.company'
    #cuentas para las CXC
    cargalargoplazo = fields.Many2one(comodel_name='account.account')
    abonolargoplazo = fields.Many2one(comodel_name='account.account')
    cargacortoplazo = fields.Many2one(comodel_name='account.account')
    abonarcortoplazo = fields.Many2one(comodel_name='account.account')
    compensacion_journal_id=fields.Many2one(comodel_name='account.journal')
    
    #cuentas para las aplicacion de pagos
    operativo_especial_cargo_account_id=fields.Many2one(comodel_name='account.account',string='Cargo de gastos operativos')
    operativo_especial_abono_account_id=fields.Many2one(comodel_name='account.account',string='Abono de gastos operativos')
    administrativo_especial_cargo_account_id=fields.Many2one(comodel_name='account.account',string='Cargo de gastos administrativos')
    administrativo_especial_abono_account_id=fields.Many2one(comodel_name='account.account',string='Abono de gastos administrativos')
    inversion_especial_cargo_account_id=fields.Many2one(comodel_name='account.account',string='Cargo de inversion en territorio')
    inversion_especial_abono_account_id=fields.Many2one(comodel_name='account.account',string='Abono de inversion en territorio')
    
    operativo_especifico_cargo_account_id=fields.Many2one(comodel_name='account.account',string='Cargo de gastos operativos')
    operativo_especifico_abono_account_id=fields.Many2one(comodel_name='account.account',string='Abono de gastos operativos')
    administrativo_especifico_cargo_account_id=fields.Many2one(comodel_name='account.account',string='Cargo de gastos administrativos')
    administrativo_especifico_abono_account_id=fields.Many2one(comodel_name='account.account',string='Abono de gastos administrativos')
    inversion_especifico_cargo_account_id=fields.Many2one(comodel_name='account.account',string='Cargo de inversion en territorio')
    inversion_especifico_abono_account_id=fields.Many2one(comodel_name='account.account',string='Abono de inversion en territorio')
    
    #departmento con lo que se calcula la planilla
    planilla_unidad_id=fields.Many2one(comodel_name='hr.department',string='Unidad a la que se le asocian las planillas')


    
class asientocontable(models.Model):
    _inherit = 'account.move'
    name = fields.Char(string="Name")
    compensacion = fields.Boolean(string="Diario de compensacion", related='journal_id.compensacion')
    compensacion_conciliado=fields.Boolean("Conciliado")
    compensacion_comentario=fields.Char("Comentario conciliacion")

class compensacion_journal(models.Model):
    _inherit = 'account.journal'
    compensacion = fields.Boolean("Diario de compensacion")

class payment_asignacion(models.Model):
    _inherit = 'account.payment'
    prueba = fields.Char(string="Prueba")
    x_letras = fields.Char(string="Cantidad")
    x_fecha = fields.Char(string="Fecha",compute='fechas')

    def aplica(self):
        for r in self:        
            for invoice in r.invoice_ids:
                desembolso = self.env['fiaes.compensacion.desembolso.desembolso'].search([('invoice_id' , '=', invoice.id)],limit=1)
                if desembolso:
                    proyecto = self.env['fiaes.compensacion.proyecto'].search([('id' , '=', desembolso.projecto_id.id)],limit=1)
                    if proyecto:
                        proyecto.disponible_sin_gastos = proyecto.disponible_sin_gastos + r.amount
    
    @api.one
    @api.depends('payment_date')
    def fechas(self):
        for r in self:
            anio = r.payment_date.year
            aniofecha = str(anio)
            months = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
            days =("uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve","diez","once","doce","trece","catorce","quince","diesciseis","diecisiete","dieciocho","diecinueve","veinte","ventiuno","veintidos","veintitres","veinticuatro","veinticinco","veintiseis","veintisiete","veintiocho","veintinueve","treinta","treinta y uno")
            day = days[r.payment_date.day-1]
            month = months[r.payment_date.month -1]
            #quemado
            if aniofecha == '2019':
                x = 'dos mil diecinueve'
            if aniofecha == '2020':
                x = 'dos mil veinte'
            if aniofecha == '2021':
                x = 'dos mil ventiuno'
            if aniofecha == '2022':
                x = 'dos mil veintidos'
            r.x_fecha = "a los " + day + " dias del mes de " + month +" de "+ x 
                                  
class account_asignacion(models.Model):
    _inherit = 'account.invoice'
    prueba = fields.Char(string="Prueba")

    def aplica(self):
        for r in self:
            desembolso = self.env['fiaes.compensacion.desembolso.desembolso'].search([('invoice_id' , '=', r.id)],limit=1)
            if desembolso:        
                proyecto = self.env['fiaes.compensacion.proyecto'].search([('id' , '=', desembolso.projecto_id.id)],limit=1)
                if proyecto:
                    proyecto.disponible_sin_gastos = proyecto.disponible_sin_gastos + r.amount_total



