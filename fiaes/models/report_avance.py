from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.safe_eval import safe_eval
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__) 


class reporteAvancek(models.Model):
    _name='fiaes.reporte.avance'
    _description='Reporte de cumplimiento mensual de actividades'
    _inherit=['mail.thread']
    name= fields.Char(string="Name", compute='_compute_name')
    actividad_ids = fields.One2many(comodel_name='fiaes.reporte.actividad',inverse_name='report_id')
    planunidad_id=fields.Many2one(comodel_name='fiaes.planunidad')
    fecha = fields.Date(string="Fecha")
    objetivos_ids = fields.One2many(comodel_name='fiaes.reporte.objetivos', inverse_name='objetivo_id')
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado',default='Borrador',track_visibility=True)
    avance_id = fields.One2many(comodel_name='fiaes.reporte.actividad', inverse_name='report_id')

    @api.one
    def aprobar(self):
        for r in self:
            r.state='Aprobado'
            for a in r.actividad_ids:
                a.state = r.state
                #mover firmado por firmado calculado
            
    
    @api.one
    def regresar(self):
        for r in self:
            r.state='Borrador'
            for a in r.actividad_ids:
                a.state = r.state
    
    @api.one
    def cancelar(self):
        for r in self:
            r.state='Cancelado'
            for a in r.actividad_ids:
                a.state = r.state


    
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
                    dic={}
                    dic["name_objetivo"]=o.id
                    dic["objetivo_id"]=r.id
                    obj=self.env['fiaes.reporte.avance'].search([('planunidad_id','=',r.planunidad_id.id)])
                    if obj:
                        self.env['fiaes.reporte.objetivos'].create(dic)
                    for i in o.actividad_line:
                        dic={}
                        dic["name_actividad"]=i.id
                        dic["proyecto"]=i.proyecto.id
                        dic["actividad_id"]=i.id
                        dic["peso"]=i.peso
                        dic["porcentaje"]=i.porcentaje
                        dic["report_id"]=r.id
                        dic["state"]=r.state
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
    porcentaje = fields.Float(string="Porcentaje avance(%)")
    totalAvance = fields.Float(string="Porcentaje total avance(%)")
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado')
    

    @api.one
    @api.constrains('porcentaje', 'state')
    def _check_avance(self):
        totalAvance = 0.0
        for r in self:
            if r.state == 'Aprobado':
        #obtener los previos a la fecha y los ordeno por fecha descendente
                _logger.info('se cumplio la condicion')
                fecha = self.env['fiaes.reporte.avance'].search([('fecha','<',r.report_id.fecha),('planunidad_id','=',r.report_id.planunidad_id.id)],order="fecha desc", limit=1)
                if fecha:
                    actividad = self.env['fiaes.reporte.actividad'].search([('actividad_id','=',r.actividad_id.id),('report_id','=',fecha.id)])
                    if actividad:
                        _logger.info('condicion actividad')
                        if r.porcentaje <= actividad.porcentaje:
                            _logger.info('condicion porcentajes')
                            raise ValidationError("El avance no puede ser menor al reporte anterior")
                        if r.porcentaje > 100:
                            raise ValidationError("El avance no puede ser mayor a 100")
            #limite = 0.0
        #for r in self:
        #    limite = limite + r.porcentaje
        #    r.totalAvance = limite
        #    if r.porcentaje < r.totalAvance:
        #        _logger.info('si es menor el nuevo porcentaje')
        #        raise ValidationError("El avance no puede ser menor al reporte anterior")
        #    if r.totalAvance > 100.00:
        #        _logger.info('el acvance es mayor a 100')
        #        raise ValidationError("El avance no puede ser mayor a 100")
                

class report_objetivos(models.Model):
    _name='fiaes.reporte.objetivos'
    _description='reporte de objetivos'
    objetivo_id=fields.Many2one(comodel_name='fiaes.reporte.avance')
    name_objetivo=fields.Many2one(comodel_name='fiaes.poaobjetivos', string="NombreObjetivo")
    porcentajeTotal=fields.Float(compute="calcularPorcentaje", store=False)

    @api.one
    def calcularPorcentaje(self):
        total = 0.0
        for r in self:
            reporte=self.env['fiaes.reporte.avance'].search([('id','=',r.objetivo_id.id)],limit=1)
            for a in reporte.actividad_ids:
                _logger.info('r id:'+ str(r.name_objetivo.id)+' a.id'+str(a.actividad_id.objetivopoa_id.id))
                if r.name_objetivo.id == a.actividad_id.objetivopoa_id.id:
                    _logger.info('se cumplio la condicion')
                    total=total+((a.actividad_id.peso * a.porcentaje)/100)   #esto entre el peso total = porcentaje de avaqnce
                    _logger.info('se cumplio la condicion' +str(total))
            r.porcentajeTotal=total
            
