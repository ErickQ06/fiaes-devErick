# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta,date
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__) 

class reasignacionUnidad(models.Model):
    _name = 'fiaes.reasignacion.planunidad'
    _inherit= ['mail.thread']
    name = fields.Char(string="Name")
    descripcion  = fields.Char(string="Descripcion ")
    planunidad_id= fields.Many2one(string="Plan unidad", comodel_name='fiaes.planunidad')
    state = fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Proceso', 'Proceso')
                                        ,('Validar', 'Validar')]
                                        , string='Estado',default='Borrador',track_visibility=True)
    disponible_line = fields.One2many(comodel_name='fiaes.asignacion.disponible',inverse_name='reasignacion_id')
    actividad_line = fields.One2many(string="Actividad",comodel_name='fiaes.poaactividad.copy',inverse_name='reasignacion_id')
    insumo_line = fields.One2many(comodel_name='fiaes.insumo.copy',inverse_name='reasignacion_id')
    x_fecha= fields.Date("actual",compute='fecha1')
    
    @api.one
    def fecha1(self):
        for r in self:
            day = date.today()
            r.x_fecha = day
    
    @api.one
    def proceso(self):
        for r in self:
            r.state='Proceso'
            domain = [('planunidad_id', '=', r.planunidad_id.id)]
            lines = self.env['fiaes.planunidad.disponible'].search(domain)
            for line in lines:
                dic={}
                dic['planunidad_id']=line.planunidad_id.id
                dic['proyecto_id']=line.proyecto_id.id
                dic['fuente_id']=line.fuente_id.id
                dic['monto']=line.monto
                dic['monto_ajustado']=0.0
                dic['reasignacion_id']=r.id
                self.env['fiaes.asignacion.disponible'].create(dic)
            domain = [('planunidad_id', '=', r.planunidad_id.id)]
            actividad = self.env['fiaes.poaactividad'].search(domain)
            for a in actividad:
                if not a.deshabili:
                    dic={}
                    dic['original_id']=a.id
                    dic['name']=a.name
                    dic['descripcion']=a.descripcion
                    dic['proyecto']=a.proyecto.id
                    dic['objetivopoa_id']=a.objetivopoa_id.id
                    dic['planunidad_id']=a.planunidad_id.id
                    dic['prioridad']=a.prioridad
                    dic['fecha_inicial']=a.fecha_inicial
                    dic['fecha_final']=a.fecha_final
                    dic['state']='Copiado'
                    dic['reasignacion_id']=r.id
                    dic['deshabili']=a.deshabili                    
                    line=self.env['fiaes.poaactividad.copy'].create(dic) 
                    domain2 = [('actividad_id', '=', a.id)]
                    insumos = self.env['fiaes.insumo'].search(domain2)    
                    for insumo in insumos:
                        if not insumo.deshabili:
                            _logger.info("entro")
                            dic2={}
                            dic2['original_id']=insumo.id
                            dic2['name']=insumo.name
                            dic2['categoria']=insumo.categoria.id
                            dic2['actividad_id']= line.id
                            dic2['preciouni']=insumo.preciouni
                            dic2['cantidad']=insumo.cantidad
                            dic2['total']=insumo.total
                            dic2['mes']=insumo.mes
                            dic2['fuente']=insumo.fuente.id
                            dic2['cuenta_id']=insumo.cuenta_id.id
                            dic2['ejecutado']=insumo.ejecutado
                            dic2['reasignacion_id']=r.id
                            dic2['state']='Copiado'
                            line2=self.env['fiaes.insumo.copy'].create(dic2) 
                    
    @api.one
    def validar(self):
        for r in self:
            r.state='Validar'
            for a in r.actividad_line:
                if a.state == 'Deshabilitado':
                    actividad = self.env['fiaes.poaactividad'].browse(a.original_id)
                    actividad.deshabili = True
                    for insumo in actividad.insumo_line:
                        insumo.deshabili = True
                        disponible = self.env['fiaes.planunidad.disponible'].search([('planunidad_id', '=', r.planunidad_id.id),('proyecto_id', '=' , actividad.proyecto.id),('fuente_id','=', insumo.fuente.id )],limit=1)  
                        if disponible:
                            disponible.monto = disponible.monto + insumo.total                        
                        else:
                            dic={}
                            dic['planunidad_id']=r.planunidad_id.id
                            dic['proyecto_id']=actividad.proyecto.id
                            dic['fuente_id']=insumo.fuente.id
                            dic['monto']=insumo.total
                            self.env['fiaes.planunidad.disponible'].create(dic)
                if a.state=='Nuevo':
                    dica={}
                    dica['name']=a.name
                    dica['descripcion']=a.descripcion
                    dica['proyecto']=a.proyecto.id
                    dica['objetivopoa_id']=a.objetivopoa_id.id
                    dica['planunidad_id']=r.planunidad_id.id
                    dica['prioridad']=a.prioridad
                    dica['fecha_inicial']=a.fecha_inicial
                    dica['fecha_final']=a.fecha_final
                    dica['extemp']=True
                    dica['deshabili']=False
                    actividad=self.env['fiaes.poaactividad'].create(dica)
                    for insumo in a.insumo_line:
                        dics={}
                        dics['name']=insumo.name
                        dics['categoria']=insumo.categoria.id
                        dics['actividad_id']=actividad.id
                        dics['preciouni']=insumo.preciouni
                        dics['cantidad']=insumo.cantidad
                        dics['mes']=insumo.mes
                        dics['fuente']=insumo.fuente.id
                        dics['cuenta_id']=insumo.cuenta_id.id
                        dics['extemp']=True
                        dics['deshabili']=False
                        self.env['fiaes.insumo'].create(dics)
                        disponible = self.env['fiaes.planunidad.disponible'].search([('planunidad_id', '=', r.planunidad_id.id),('proyecto_id', '=' ,a.proyecto.id),('fuente_id','=', insumo.fuente.id )],limit=1)  
                        if disponible:
                            disponible.monto = disponible.monto - insumo.total                        
                        else:
                            dic={}
                            dic['planunidad_id']=r.planunidad_id.id
                            dic['proyecto_id']=actividad.proyecto.id
                            dic['fuente_id']=insumo.fuente.id
                            dic['monto']=insumo.total*-1
                            self.env['fiaes.planunidad.disponible'].create(dic)
                if a.state=='Copiado':
                    for insumo in a.insumo_line:
                        if insumo.state=='Nuevo':
                            dics={}
                            dics['name']=insumo.name
                            dics['categoria']=insumo.categoria.id
                            dics['actividad_id']=insumo.actividad_id.original_id
                            dics['preciouni']=insumo.preciouni
                            dics['cantidad']=insumo.cantidad
                            dics['mes']=insumo.mes
                            dics['fuente']=insumo.fuente.id
                            dics['cuenta_id']=insumo.cuenta_id.id
                            dics['extemp']=True
                            dics['extedeshabilimp']=False
                            self.env['fiaes.insumo'].create(dics)
                            disponible = self.env['fiaes.planunidad.disponible'].search([('planunidad_id', '=', r.planunidad_id.id),('proyecto_id', '=' ,a.proyecto.id),('fuente_id','=', insumo.fuente.id )],limit=1)  
                            if disponible:
                                disponible.monto = disponible.monto - insumo.total                        
                            else:
                                dic={}
                                dic['planunidad_id']=r.planunidad_id.id
                                dic['proyecto_id']=insumo.actividad_id.proyecto.id
                                dic['fuente_id']=insumo.fuente.id
                                dic['monto']=insumo.total*-1
                                self.env['fiaes.planunidad.disponible'].create(dic)
                        if insumo.state=='Deshabilitado':
                            original=self.env['fiaes.insumo'].browse(insumo.original_id)
                            original.deshabili=True
                            disponible = self.env['fiaes.planunidad.disponible'].search([('planunidad_id', '=', r.planunidad_id.id),('proyecto_id', '=' , a.proyecto.id),('fuente_id','=', insumo.fuente.id )],limit=1)  
                            if disponible:
                                disponible.monto = disponible.monto + insumo.total                        
                            else:
                                dic={}
                                dic['planunidad_id']=r.planunidad_id.id
                                dic['proyecto_id']=a.proyecto.id
                                dic['fuente_id']=insumo.fuente.id
                                dic['monto']=insumo.total
                                self.env['fiaes.planunidad.disponible'].create(dic)
            disponibles=self.env['fiaes.planunidad.disponible'].search([('planunidad_id', '=', r.planunidad_id.id)])
            for d in disponibles:
                if d.monto<0:
                    raise ValidationError('El proyecto:'+d.proyecto_id.name+' y fuente:'+d.fuente_id.name+' esta sobregirada')


    
class Actividadpoa(models.Model):
    _name = 'fiaes.poaactividad.copy'
  
    name =  fields.Char(string="Actividad",track_visibility=True)
    descripcion = fields.Text(string="Descripcion",track_visibility=True)   
    proyecto = fields.Many2one(comodel_name='project.project', string="Proyecto")  
    objetivopoa_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',string="Objetivo Operativo",track_visibility=True)
    responsable = fields.Many2many(comodel_name='res.users',string="Responsable",relation="actividad_responsables",track_visibility=True)
    coordina = fields.Many2many(comodel_name='res.users',string="Coodina con",relation="actividad_coordina",track_visibility=True)
    insumo_line = fields.One2many(comodel_name='fiaes.insumo.copy', inverse_name='actividad_id') 
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad', string="Plan unidad",store=True)
    unidad = fields.Many2one(comodel_name='hr.department',related='planunidad_id.unidad',store=True)
    poa_id=fields.Many2one(comodel_name='fiaes.poa',related='planunidad_id.poa_id',store=True)
    total = fields.Float(string="Total")
    prioridad=fields.Integer("Prioridad")
    fecha_inicial=fields.Date("Fecha de inicio")
    fecha_final=fields.Date("Fecha de finalizacion")
    state = fields.Selection(selection=[('Copiado', 'Copiado')
                                        ,('Nuevo', 'Nuevo')
                                        ,('Deshabilitado', 'Deshabilitado')]
                                        , string='Estado',default='Nuevo')
    reasignacion_id = fields.Many2one(comodel_name='fiaes.reasignacion.planunidad')
    extemp = fields.Boolean(string="Extemporaneo")
    deshabili = fields.Boolean(string="Habilitado")
    state1 = fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Proceso', 'Proceso')
                                        ,('Validar', 'Validar')]
                                        , string='Estado',default='Borrador',related='reasignacion_id.state',track_visibility=True)
    original_id = fields.Integer(string="id original")
    insumo_id = fields.Many2many(comodel_name='fiaes.planunidad', string="Insumos")

    @api.one
    def habilitar(self):
        for r in self:
            r.state='Copiado'
            for x in r.insumo_line:
                x.habilitar()
            
    @api.one
    def deshabilitar(self):
        for r in self:
            r.state='Deshabilitado'
            for x in r.insumo_line:
                x.deshabilitar()
                    
            
    
class insumo(models.Model):
    _name = 'fiaes.insumo.copy'
    name = fields.Char(string="Bien/Servicio")
    categoria = fields.Many2one(comodel_name='fiaes.insumo.categoria', string='Categorias de insumos')
    actividad_id = fields.Many2one(comodel_name='fiaes.poaactividad.copy')
    preciouni = fields.Float(string="Precio Unitario")
    cantidad = fields.Float(string="Cantidad")
    total = fields.Float(string="Total", compute="cant_total",store=True)
    mes = fields.Selection([('01','Enero'),('02','Febrero'),('03','Marzo'),('04','Abril'),('05','Mayo'),('06','Junio'),('07','Julio'),('08','Agosto'),('09','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')])
    fuente = fields.Many2one(comodel_name='fiaes.fuente', string='Fuente de financiamiento')
    cuenta_id = fields.Many2one(comodel_name='account.account', string="Cuenta")
    reasignacion_id = fields.Many2one(comodel_name='fiaes.reasignacion.planunidad')
    ejecutado=fields.Boolean("Ejecutado")         
    state = fields.Selection(selection=[('Copiado', 'Copiado')
                                        ,('Nuevo', 'Nuevo')
                                        ,('Deshabilitado', 'Deshabilitado')]
                                        , string='Estado',default='Nuevo')
    extemp = fields.Boolean(string="Extemporaneo")
    deshabili = fields.Boolean(string="deshabilitado")
    state1 = fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Proceso', 'Proceso')
                                        ,('Validar', 'Validar')]
                                        , string='Estado',default='Borrador',related='reasignacion_id.state',track_visibility=True)
    original_id = fields.Integer(string="id original")
    
    @api.one
    def habilitar(self):
        for r in self:
            r.state='Copiado'
            disponible = self.env['fiaes.asignacion.disponible'].search([('reasignacion_id', '=', r.reasignacion_id.id),('proyecto_id', '=' , r.actividad_id.proyecto.id),('fuente_id','=', r.fuente.id )],limit=1)  
            if disponible:
                disponible.monto_ajustado = disponible.monto_ajustado - r.total                        
            else:
                dic={}
                dic['planunidad_id']=r.actividad_id.planunidad_id.id
                dic['proyecto_id']=r.actividad_id.proyecto.id
                dic['fuente_id']=r.fuente.id
                dic['monto_ajustado']=-r.total
                dic['reasignacion_id']=r.reasignacion_id.id
                self.env['fiaes.asignacion.disponible'].create(dic)
            
    @api.one
    def deshabilitar(self):
        for r in self:
            r.state='Deshabilitado'
            disponible = self.env['fiaes.asignacion.disponible'].search([('reasignacion_id', '=', r.reasignacion_id.id),('proyecto_id', '=' , r.actividad_id.proyecto.id),('fuente_id','=', r.fuente.id )],limit=1)  
            if disponible:
                _logger.info('El disponible si existe:'+str(r.reasignacion_id.id) +' proyecto:'+ str(r.actividad_id.proyecto.id)+ '  fuente:'+str(r.fuente.id) )
                disponible.monto_ajustado = disponible.monto_ajustado + r.total
            else:
                _logger.info('El disponible no existe')
                dic={}
                dic['planunidad_id']=r.actividad_id.planunidad_id.id
                dic['proyecto_id']=r.actividad_id.proyecto.id
                dic['fuente_id']=r.fuente.id
                dic['monto_ajustado']=r.total
                dic['reasignacion_id']=r.reasignacion_id.id
                _logger.info(dic)
                self.env['fiaes.asignacion.disponible'].create(dic)
                    
    @api.model
    def create(self, values):
        # Override the original create function for the res.partner model
        record = super(insumo, self).create(values)
        #enviando el correo de confirmacion
        #creando las alertas
        if record.state=='Nuevo':
            disponible = self.env['fiaes.asignacion.disponible'].search([('reasignacion_id', '=', record.reasignacion_id.id),('proyecto_id', '=' , record.actividad_id.proyecto.id),('fuente_id','=', record.fuente.id )],limit=1)  
            if disponible:
                disponible.monto_ajustado = disponible.monto_ajustado - record.total                        
            else:
                dic={}
                dic['planunidad_id']=record.actividad_id.planunidad_id.id
                dic['proyecto_id']=record.actividad_id.proyecto.id
                dic['fuente_id']=record.fuente.id
                dic['monto_ajustado']=-record.total
                dic['reasignacion_id']=record.reasignacion_id.id
                self.env['fiaes.asignacion.disponible'].create(dic)
            return record
    
    @api.multi
    def unlink(self):
        for r in self:
            if r.state not in ('Nuevo'):
                raise ValidationError('No se puede eliminar un insumo que no sea nuevo')
            else:
                disponible = self.env['fiaes.asignacion.disponible'].search([('reasignacion_id', '=', r.reasignacion_id.id),('proyecto_id', '=' , r.actividad_id.proyecto.id),('fuente_id','=', r.fuente.id )],limit=1)  
                if disponible:
                    _logger.info('El disponible si existe:'+str(r.reasignacion_id.id) +' proyecto:'+ str(r.actividad_id.proyecto.id)+ '  fuente:'+str(r.fuente.id) )
                    disponible.monto_ajustado = disponible.monto_ajustado + r.total
        return models.Model.unlink(self)
    
    
    @api.one
    @api.depends('cantidad','preciouni')
    def cant_total(self):
        for r in self:
            r.total=r.preciouni*r.cantidad



class disponible_asignacion(models.Model):
    _name='fiaes.asignacion.disponible'
    name = fields.Char(string="Name")
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad')
    monto = fields.Float(string="Monto")
    monto_ajustado = fields.Float(string="Monto ajustado")
    proyecto_id = fields.Many2one(string="Proyecto",comodel_name='project.project')
    fuente_id = fields.Many2one(string="Fuente",comodel_name='fiaes.fuente')
    reasignacion_id = fields.Many2one(comodel_name='fiaes.reasignacion.planunidad')