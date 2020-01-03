# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class plan_disponible(models.Model):
    _name ='fiaes.planunidad.disponible'
    name = fields.Char(string="Name")
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad')
    monto = fields.Float(string="Monto")
    proyecto_id = fields.Many2one(string="Proyecto",comodel_name='project.project')
    fuente_id = fields.Many2one(string="Fuente",comodel_name='fiaes.fuente')
    #reasignacion_id = fields.Many2one(comodel_name='fiaes.reasignacion.planunidad')
    state = fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Proceso', 'Proceso')
                                        ,('Validar', 'Validar')]
                                        , string='Estado',default='Borrador',track_visibility=True)
    
class variables_fiaes(models.Model):
    _name ='fiaes.company.variables'
    name = fields.Char("Name")
    company_id = fields.Many2one(comodel_name='res.company')
    
class company_Variables(models.Model):
    _inherit= 'res.company'
    variable_line = fields.One2many(comodel_name='fiaes.company.variables', inverse_name='company_id')    
    tipo_line = fields.One2many(comodel_name='fiaes.company.tipo', inverse_name='company_id')
    
    
class company_tipo(models.Model):
    _name='fiaes.company.tipo'
    name = fields.Char("Nombre")
    formula = fields.Char("Formula")
    company_id = fields.Many2one(comodel_name='res.company')
    tipo = fields.Selection(selection=[('Mensual', 'Mensual')
                                        ,('Mes especifico', 'Mes especifico')]
                                        , string='Tipo',default='Mensual')
    mes = fields.Selection([('01','Enero'),('02','Febrero'),('03','Marzo'),('04','Abril'),('05','Mayo'),('06','Junio'),('07','Julio'),('08','Agosto'),('09','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')]) 
    cuenta_id = fields.Many2one(comodel_name='account.account', string="Cuenta")
    
class variante_valor(models.Model):
    _name ='fiaes.variante.valor'
    name = fields.Char("Nombre",related='variante_id.name')
    variante_id = fields.Many2one(comodel_name='fiaes.company.variables')
    valor = fields.Float("Valor")
    contract_id = fields.Many2one(comodel_name='hr.contract')

class variante_contract(models.Model):
    _inherit='hr.contract'    
    line_valor = fields.One2many(string="Variante",comodel_name='fiaes.variante.valor',inverse_name='contract_id')
    perfil_id=fields.Many2one(string="Perfil de prorrateo",comodel_name='fiaes.prorrateo.perfil')

#tabla de prorrateo
class tabla_prorrateo(models.Model):
    _name='fiaes.prorrateo'
    name=fields.Char("Tabla de prorrateo")
    comentario=fields.Text("Descripcion")
    line_ids=fields.One2many(comodel_name='fiaes.prorrateo.line', inverse_name='prorrateo_id')
    
    
    @api.model
    def create(self, values):
        # Override the original create function for the res.partner model
        record = super(tabla_prorrateo, self).create(values)
        total=0
        for r in record.line_ids:
            total=total+r.porcentaje
        if total!=100.00:
            raise ValidationError('La suma de los porcentajes debe ser 100')
        return record

    @api.multi
    def write(self, values):
        # Override the original create function for the res.partner model
        record = super(tabla_prorrateo, self).write(values)
        for r in self:
            total=0
            for rl in r.line_ids:
                total=total+rl.porcentaje
            if total!=100.00:
                raise ValidationError('La suma de los porcentajes debe ser 100')
        return record
    

class tabla_prorrateo_detalle(models.Model):
    _name='fiaes.prorrateo.line'
    name=fields.Char("Fuente",relate='fuente_id.name')
    fuente_id = fields.Many2one(string="Fuente",comodel_name='fiaes.fuente')
    proyecto_id = fields.Many2one(string="Proyecto",comodel_name='project.project')
    porcentaje=fields.Float("% del salario",digits=(20,10))
    prorrateo_id=fields.Many2one(string="Prorrateo",comodel_name='fiaes.prorrateo')




#tabla de prorrateo
class tabla_prorrateo_perfil(models.Model):
    _name='fiaes.prorrateo.perfil'
    name=fields.Char("Perfil de prorrateo")
    comentario=fields.Text("Descripcion")
    line_ids=fields.One2many(comodel_name='fiaes.prorrateo.perfil.line', inverse_name='perfil_id')

class tabla_prorrateo_perfil_detalle(models.Model):
    _name='fiaes.prorrateo.perfil.line'
    name=fields.Char("Calculo",relate='fuente_id.name')
    tipo_id = fields.Many2one(string="Tipo Calculo",comodel_name='fiaes.company.tipo')
    perfil_id=fields.Many2one(string="Perfil",comodel_name='fiaes.prorrateo.perfil')
    cuenta_id=fields.Many2one(string="Cuenta",comodel_name='account.account')
    prorrateo_id=fields.Many2one(string="Prorrateo",comodel_name='fiaes.prorrateo')
