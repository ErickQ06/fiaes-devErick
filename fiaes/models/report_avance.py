from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.safe_eval import safe_eval
from odoo import SUPERUSER_ID


class reporteAvancek(models.Model):
    _name='fiaes.reporte.avance'
    _description='Reporte de cumplimiento mensual de actividades'
    _inherit=['mail.thread']
    name= fields.Char(string="Name", compute='_compute_name')
    actividad_ids = fields.One2many(comodel_name='fiaes.reporte.actividad',inverse_name='report_id')
    planunidad_id=fields.Many2one(comodel_name='fiaes.planunidad')
    fecha = fields.Date(string="Fecha")
    
    @api.one
    @api.depends('actividad_ids','fecha')
    def _compute_name(self):
        for r in self:
            if r.planunidad_id:
                if r.fecha:
                    r.name=r.planunidad_id.name+' '+r.fecha.strftime("%m/%d/%Y")
    @api.one
    def generate_items(self):
        for r in self: 
            if r.planunidad_id:
                for o in r.planunidad_id.objetivo_line:
                    for i in o.actividad_line:
                        dic={}
                        dic["name_actividad"]=i.id
                        dic["proyecto"]=i.proyecto.id
                        dic["peso"]=i.peso
                        dic["procentaje"]=i.porcentaje
                        dic["report_id"]=r.id
                        line=self.env['fiaes.reporte.avance'].search([('planunidad_id','=',r.planunidad_id.id)])
                        if line:
                            self.env['fiaes.reporte.actividad'].create(dic)

class report_resultadok(models.Model):
    _name='fiaes.reporte.actividad'
    _description='Actividades'
    actividad_id=fields.Many2one(comodel_name='fiaes.poaactividad')
    objetivopoa_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',string="Objetivo Operativo")
    proyecto = fields.Many2one(comodel_name='project.project', string="Proyecto")
    name_actividad=fields.Many2one(comodel_name='fiaes.poaactividad', string="nombreActividad")
    peso = fields.Float(string="peso")
    report_id= fields.Many2one(comodel_name='fiaes.reporte.avance')
    porcentaje = fields.Float(string="Porcentaje avance(%)", required=True)