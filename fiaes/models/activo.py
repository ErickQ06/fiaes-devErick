# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID



class activo_property(models.Model):
    _name='fiaes.activo_property'
    _description='Aspecto a Revisar'
    name=fields.Char("Atributo")
    valor=fields.Char("Valor")
    activo_id=fields.Many2one(comodel_name='account.asset.asset', string='Activo')


class activo_property(models.Model):
    _inherit='account.asset.category'
    codigo=fields.Char("Codigo")
    

class activo_mantenimiento(models.Model):
    _inherit='maintenance.equipment'
    activo_id=fields.Many2one(comodel_name='account.asset.asset', string='Activo asociado')

class activofijo(models.Model):
    _inherit='account.asset.asset'
    responsable_id=fields.Many2one(comodel_name='hr.employee', string='Responsable')
    ubicacion_id=fields.Many2one(comodel_name='stock.location', string='Ubicacion')
    propiedad_ids=fields.One2many('fiaes.activo_property','activo_id', 'Propiedades')
    marca=fields.Char("Marca")
    modelo=fields.Char("Modelo")
    parent_id=fields.Many2one(comodel_name='account.asset.asset', string='Activo Padre')
    child_ids=fields.One2many('account.asset.asset', 'parent_id' , 'Activo Padre')
    capitalizable=fields.Selection(selection=[('Capitalizable', 'Capitalizable')
                                        ,('No Capitalizable', 'No Capitalizable')]
                                        , string='Tipo de Activo',default='Capitalizable')
    def create_equipo(self):
        for record in self:
            self.env['maintenance.equipment'].create({'name':record.name,'effective_date':record.date,'equipment_assign_to':'employee','active':True})



    def set_codigo(self):
        for record in self:
            if not record.code:
                codigo='FIAES'
                if record.capitalizable=='Capitalizable':
                    codigo=codigo+'-1'
                    codigo=codigo+''+record.category_id.codigo
                    codigo=codigo+''+self.env['ir.sequence'].next_by_code('fiaes.activo.capitalizable')
                else:
                    codigo=codigo+'-0'
                    codigo=codigo+''+record.category_id.codigo
                    codigo=codigo+''+self.env['ir.sequence'].next_by_code('fiaes.activo.nocapitalizable')
                record.write({'code':codigo})
