# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class vehiculo(models.Model):
    _inherit='fleet.vehicle'
    marca_id=fields.Many2one(comodel_name='fleet.vehicle.model.brand', related='model_id.brand_id',string='Marca',store='false')
    clase_id=fields.Many2one(comodel_name='fiaes.vehiculo_clase', string='Clase')
    tipo_id=fields.Many2one(comodel_name='fiaes.vehiculo_tipo', string='Tipo')
    motor=fields.Char("Motor #")
    chasis=fields.Char("Chasis #")
    activo_id=fields.Many2one(comodel_name='account.asset.asset', string='Activo')
    tarjeta=fields.Binary("Tarjeta de circulacion")
    servicios_km_ids=fields.One2many('fiaes.vehiculo_servicio','vehicle_id', 'Kilometrajes por servicio')

class servicio_kilometraje(models.Model):
    _name = 'fiaes.vehiculo_servicio'
    _description= 'Kilometrajes por servicio'
    name=fields.Char("Comentario")
    servicio=fields.Many2one(comodel_name='fleet.service.type', string='Servicio')
    kilometraje=fields.Integer("Kilometraje entre servicios")
    vehicle_id=fields.Many2one(comodel_name='fleet.vehicle', string='Vehiculo')
    ultimo_kilometraje=fields.Integer("Kilometraje entre servicios")


class usovehiculo(models.Model):
    _name = 'fiaes.solicitud_vehiculo'
    _inherit= ['mail.thread']
    _description= 'Solicitud de vehiculo'
    name=fields.Char("Evento",required=True)
    solicitante_tipo=fields.Selection(selection=[('Empleado', 'Empleado')
                                        ,('Contacto', 'Contacto')]
                                        , string='Tipo de solicitante',required=True)
    solicitante_employee_id=fields.Many2one(comodel_name='hr.employee', string='Solicitante')
    solicitante_partner_id=fields.Many2one(comodel_name='res.partner', string='Solicitante')
    vehicle_id=fields.Many2one(comodel_name='fleet.vehicle', string='Vehiculo')
    vehicle_name=fields.Char("Vehiculo",compute='get_vehicle',store=False)
    solicitante=fields.Char(string='Solicitante',compute='get_solicitante')
    source_email=fields.Char(string='Email',compute='get_solicitante')
    fecha_solicitud=fields.Date("Fecha Solicitud",required=True)
    destino=fields.Char("Destino",required=True)
    mision_oficial=fields.Char("Mision Oficial",track_visibilty='always',required=True)
    programada=fields.Selection(selection=[('Programada', 'Programada')
                                        ,('No Programada', 'No Programada')]
                                        , string='Tipo de solicitud',required=True)
    fecha_salida=fields.Datetime("Fecha Salida")
    fecha_salida_real=fields.Datetime("Fecha y hora de Salida Real")
    fecha_regreso_esperada=fields.Datetime("Fecha Regreso estimado")
    fecha_regreso=fields.Datetime("Fecha Regreso")
    asistieron_ids=fields.Many2many(comodel_name='res.partner', string='Asistieron')
    encargado_revision_id=fields.Many2one(comodel_name='res.users', string='Encargado de revision')
    encargado_autorizacion_id=fields.Many2one(comodel_name='res.users', string='Encargado de autorizacion')
    conductor_ids=fields.Many2many(comodel_name='res.users', string='Conductores')
    odometros_ids=fields.One2many('fleet.vehicle.odometer','solicitud_id', 'Marcaciones')
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Solicitado', 'Solicitado')
                                        ,('Autorizado', 'Autorizado')
                                        ,('Asignado', 'Asignado')
                                        ,('En curso', 'En curso')
                                        ,('Finalizado', 'Finalizado')
                                        ,('Cancelado', 'Cancelado')]
                                        , string='Estado',default='Borrador',track_visibilty='always')
    def solicitar(self):
        for record in self:
            record.state='Solicitado'
            template = self.env.ref('fiaes.SolicitudVehiculo_solicitud', False)
            x=self.env['mail.template'].browse(template.id).send_mail(record.id)
            mail=self.env['mail.mail'].search([('id','=',x)])
            if mail:
                mail.write({'failure_reason':''})
                mail.send()

    def autorizar(self):
        for record in self:
            record.state='Autorizado'
            record.encargado_revision_id=self.env.user.id
            template = self.env.ref('fiaes.SolicitudVehiculo_autorizado', False)
            x=self.env['mail.template'].browse(template.id).send_mail(record.id)
            mail=self.env['mail.mail'].search([('id','=',x)])
            if mail:
                mail.write({'failure_reason':''})
                mail.send()

    def asignar(self):
        for record in self:
            record.state='Asignado'
            record.encargado_revision_id=self.env.user.id
            if not record.vehicle_id:
                raise ValidationError("Debe especificar el vehiculo asignado")
            template = self.env.ref('fiaes.SolicitudVehiculo_asignado', False)
            x=self.env['mail.template'].browse(template.id).send_mail(record.id)
            mail=self.env['mail.mail'].search([('id','=',x)])
            if mail:
                mail.write({'failure_reason':''})
                mail.send()

    def iniciar(self):
        for record in self:
            if not record.fecha_salida_real:
                raise ValidationError("Debe especificar una fecha de salida")
            if not record.asistieron_ids:
                raise ValidationError("Debe especificar quienes asisten")
            if not record.conductor_ids:
                raise ValidationError("Debe especificar quienes son los responsables")
            record.state='En curso'

    def finalizar(self):
        for record in self:
            i=0
            for detalle in record.odometros_ids:
                i=i+1
            if i>1:
                record.state='Finalizado'
            else:
                raise ValidationError('deben haber al menos dos registros')

    def cancelar(self):
        for record in self:
            record.state='Cancelado'
        template = self.env.ref('fiaes.SolicitudVehiculo_cancelado', False)
        x=self.env['mail.template'].browse(template.id).send_mail(record.id)
        mail=self.env['mail.mail'].search([('id','=',x)])
        if mail:
            mail.write({'failure_reason':''})
            mail.send()

    @api.one
    @api.depends('vehicle_id')
    def get_vehicle(self):
        for record in self:
            if record.vehicle_id:
                record.vehicle_name=record.vehicle_id.model_id.name + record.vehicle_id.license_plate

    @api.one
    @api.depends('solicitante_tipo','solicitante_employee_id','solicitante_partner_id')
    def get_solicitante(self):
        for record in self:
            if record.solicitante_tipo=='Empleado':
                if record.solicitante_employee_id:
                    record.solicitante=record.solicitante_employee_id.name
                    record.source_email=record.solicitante_employee_id.work_email
            else:
                if record.solicitante_partner_id:
                    record.solicitante=record.solicitante_partner_id.name
                    record.source_email=record.solicitante_partner_id.email



class usovehiculo_detalle(models.Model):
    _inherit = 'fleet.vehicle.odometer'
    odometro_regreso=fields.Integer("Kilometraje de llegada")
    odometro_salida=fields.Integer("Kilometraje de salida")
    fecha_salida=fields.Datetime("Fecha y hora de salida")
    fecha_regreso=fields.Datetime("Fecha y hora de llegada")
    comentario=fields.Char("Comentario")
    solicitud_id=fields.Many2one(comodel_name='fiaes.solicitud_vehiculo', string='Solicitud')
    solicitante=fields.Char(string='Solicitante',related='solicitud_id.solicitante')
    destino=fields.Char("Destino",related='solicitud_id.destino')
    mision_oficial=fields.Char("Mision Oficial",track_visibilty='always',related='solicitud_id.mision_oficial')
    conductor_id=fields.Many2one(comodel_name='res.users', string='Conductor')
    conductor_ids=fields.Many2many(comodel_name='res.users', string='Conductores',related='solicitud_id.conductor_ids')
    programada=fields.Selection(selection=[('Programada', 'Programada')
                                        ,('No Programada', 'No Programada')]
                                        , string='Tipo de solicitud',related='solicitud_id.programada')
    @api.depends('solicitud_id')
    def get_conductores(self):
        for record in self:
            i=0
            start1="["
            start2="['|',"
            separator=""
            dominio=""
            if record.solicitud_id:
                if record.solicitud_id.conductor_ids:
                    for conductor in record.solicitud_id.conductor_ids:
                        dominio=separator+"('id','=',"+str(conductor.id)+")"
                        separator=","
                        i=i+1
            if i==0:
                dominio=""
            if i==1:
                dominio=start1+dominio+"]"
            if i==2:
                dominio=start2+dominio+"]"
            record.conductor_ids = dominio

    @api.model
    def create(self, values):
        # Override the original create function for the res.partner model
        record = super(usovehiculo_detalle, self).create(values)
        #buscando registro de kilometraje
        list=self.env['fiaes.vehiculo_servicio'].search([('vehicle_id','=',record.vehicle_id.id)])
        for servicio in list:
            kmrecorridos=record.odometro_regreso-servicio.ultimo_kilometraje
            if kmrecorridos>servicio.kilometraje:
                template = self.env.ref('fiaes.MantenimientoVehiculo', False)
                self.env['mail.template'].browse(template.id).send_mail(servicio.id)
        return record


class vehiculo_clase(models.Model):
    _name='fiaes.vehiculo_clase'
    _description='Clase de vehiculo'
    name=fields.Char("Clase de vehiculo")

class vehiculo_tipo(models.Model):
    _name='fiaes.vehiculo_tipo'
    _description='Tipos de vehiculo'
    name=fields.Char("Tipo de vehiculo")


class aspectorevisar(models.Model):
    _name='fiaes.vehiculo_aspecto'
    _description='Aspecto a Revisar'
    name=fields.Char("Aspecto a revisar")

class mantenimiento(models.Model):
    _inherit='fleet.vehicle.log.services'
    solicitante_id=fields.Many2one(comodel_name='hr.employee', string='Solicitante')
    descripcion=fields.Text('Descripcion')
    marca=fields.Many2one(comodel_name='fleet.vehicle.model.brand', related='vehicle_id.marca_id',string='Marca',store='false')
    modelo=fields.Many2one(comodel_name='fleet.vehicle.model', related='vehicle_id.model_id',string='Model',store='false')
    placa=fields.Char(related='vehicle_id.license_plate',string='Placa',store='false')
    taller_id=fields.Many2one(comodel_name='res.partner', string='Taller')
    taller_contacto=fields.Char(related='taller_id.contacto',string='Contacto del taller',store='false')
    taller_direccion=fields.Char(related='taller_id.street',string='Contacto del taller',store='false')
    taller_telefono=fields.Char(related='taller_id.phone',string='Contacto del taller',store='false')
    salida_fecha=fields.Date("Fecha salida")
    salida_km=fields.Integer("Kilometraje de salida")
    salida_gas=fields.Selection(selection=[('0.25', '1/4')
                                        ,('0.5', '1/2')
                                        ,('0.75', '3/4')
                                        ,('1', 'Full')]
                                        , string='Combustible de salida')
    retorno_fecha=fields.Date("Fecha retorno")
    retorno_km=fields.Integer("Kilometraje de retorno")
    retorno_gas=fields.Selection(selection=[('0.25', '1/4')
                                        ,('0.5', '1/2')
                                        ,('0.75', '3/4')
                                        ,('1', 'Full')]
                                        , string='Combustible de regreso')
    diagnostico=fields.Text("Diagnostico")
    purchase_order_id=fields.Many2one(comodel_name='purchase.order', string='Orden de compra')
    apecto_ids=fields.Many2many(comodel_name='fiaes.vehiculo_aspecto', string='Aspectos a revisar')
    salida_encargado_id=fields.Many2one(comodel_name='hr.employee', string='Encargado de salida')
    retorno_encargado_id=fields.Many2one(comodel_name='hr.employee', string='Encargado de recepcion')
