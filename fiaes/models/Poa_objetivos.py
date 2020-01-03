from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class Objetivopoa(models.Model):
    _name = 'fiaes.poaobjetivos'
    _inherit= ['mail.thread']
    name =  fields.Char(string="Objetivo",track_visibility=True)
    objetivorer_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',string="Objetivo Padre",track_visibility=True) #relacion a la misma entidad
    descripcion = fields.Text(string="Descripcion",track_visibility=True)
    objetivopei_id = fields.Many2one(comodel_name='fiaes.objetivo', string="Objetivo estrategico")
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad', string="Plan unidad")
    poa_id = fields.Many2one(comodel_name='fiaes.poa', related='planunidad_id.poa_id', string="POA")
    vinculado_pei=fields.Boolean("Vinculado al PEI")
    indicador_line = fields.One2many(comodel_name='fiaes.poaobjetivos.indicador',inverse_name='objetivopoa_id', string='Indicadores') 
    actividad_line = fields.One2many(comodel_name='fiaes.poaactividad', inverse_name='objetivopoa_id') 
    total = fields.Float(string="Total", compute="cant_total")
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Presentado', 'Presentado')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado',required=True,default='Borrador',related='planunidad_id.state',track_visibility=True)
    
    @api.one
    @api.depends('actividad_line')
    def cant_total(self):
        total=0.0
        for r in self:
            for a in r.actividad_line:
                total=total+a.total
            r.total=total
    

class Objetivopoa_indicador(models.Model):
    _name='fiaes.poaobjetivos.indicador'
    _description='Indicadores relacionados del PEI'
    indicador_id=fields.Many2one(comodel_name='fiaes.indicador', string='Indicador')
    valor=fields.Float('Cantidad/Valor')
    supuesto=fields.Char('Supuesto') 
    objetivopoa_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',string="Objetivo Operativo",track_visibility=True)
    objetivopei_id = fields.Many2one(comodel_name='fiaes.objetivo',related="objetivopoa_id.objetivopei_id", string="Objetivo estrategico")
    uom_id=fields.Many2one("uom.uom",string="Unidad de medida",related='indicador_id.uom_id',track_visibility=True)  

class Peidnc(models.Model):
    _name = 'fiaes.dnc'     
    _inherit= ['mail.thread'] 
    name = fields.Char(string="Capacitacion solicitada",track_visibility=True)
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad', string="plan")
    objetivo = fields.Text(string="Objetivo",track_visibility=True)
    objetivopoa_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',string="Objetivo Operativo",track_visibility=True)
    dirigido = fields.Text(string="Dirigido a",track_visibility=True)
    proveedor = fields.Char(string="Proveedor",track_visibility=True)
    costo = fields.Float(string="Costo",track_visibility=True)
    participante = fields.Integer(string="Participantes",track_visibility=True)
    fuente_id = fields.Many2one(comodel_name='fiaes.fuente', string='Fuente de financiamiento')
    proyecto = fields.Many2one(comodel_name='project.project', string="Proyecto",store=True)
    unidad = fields.Many2one(comodel_name='hr.department')
    
    mes = fields.Selection([('01','Enero'),('02','Febrero'),('03','Marzo'),('04','Abril'),('05','Mayo'),('06','Junio'),('07','Julio'),('08','Agosto'),('09','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')],track_visibility=True)  
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado',required=True,default='Borrador',track_visibility=True)
    actividad_id = fields.Many2one(comodel_name='fiaes.poaactividad')
    cuenta_id = fields.Many2one(comodel_name='account.account', string="Cuenta")
    
    @api.one
    def aprobar(self):
        for r in self:
            if r.actividad_id:
                self.env['fiaes.insumo'].create({'name':r.name,'preciouni':r.costo,'cantidad':1,'actividad_id':r.actividad_id.id,'fuente':r.fuente_id.id,'cuenta_id':r.cuenta_id.id,'mes':r.mes})
                r.state='Aprobado'
    
    
    @api.one
    def regresar(self):
        for r in self:
            r.state='Borrador'
    
    @api.one
    def cancelar(self):
        for r in self:
            r.state='Cancelado'