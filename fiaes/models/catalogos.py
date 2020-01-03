# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class contacto(models.Model):
    _inherit = 'res.partner'

class profesion(models.Model):
    _name='fiaes.profesion'
    _description='Profesion asociada al empleado'
    name=fields.Char("Profesion")

class beneficiario(models.Model):
    _name='fiaes.beneficiario'
    _description='Benefiario'
    name=fields.Char("Nombre")
    empleado_id=fields.Many2one(comodel_name='hr.employee', string='Empleado')
    parentesco=fields.Selection(selection=[('Hijo/a', 'Hijo/a')
                                        ,('Padre/Madre', 'Padre/Madre')
                                        ,('Esposo/a', 'Esposo/a')
                                        ,('Otro', 'Otro')]
                                        , string='Parentesco')

class departamento(models.Model):
    _name='fiaes.departamento'
    _description='Departamento'
    name=fields.Char("Departamento")

class municipio(models.Model):
    _name='fiaes.municipio'
    _description='Municipio'
    name=fields.Char("Municipio")
    departamento=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento')

class afp(models.Model):
    _name='fiaes.afp'
    _description='AFP'
    name=fields.Char("AFP")



class empleado(models.Model):
    _inherit = 'hr.employee'
    codigo=fields.Integer("Codigo empleado")
    nombres=fields.Char("Nombres")
    apellidos=fields.Char("Apellidos")
    name=fields.Char("Nombre",compute='compute_name')
    dui=fields.Char("DUI")
    nit=fields.Char("NIT")
    licencia=fields.Char("Licencia")
    fecha_licencia=fields.Date("Fecha vencimiento licencia")
    tipo_sangre=fields.Char("Tipo de sangre")
    profesion_id=fields.Many2one(comodel_name='fiaes.profesion', string='Profesion')
    departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento')
    municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio')
    afp_id=fields.Many2one(comodel_name='fiaes.afp', string='AFP')
    direccion=fields.Char("Direccion")
    beneficiarios_ids=fields.One2many('fiaes.beneficiario','empleado_id', 'Beneficiarios')
    fecha_ingreso=fields.Date("Fecha de Ingreso")
    fecha_retiro=fields.Date("Fecha de Retiro")
    causas_despido=fields.Text("Causas de retiro")
    cuenta_bancaria=fields.Char("Cuenta Bancaria")
    marital=fields.Selection(selection=[('single', 'Soltero')
                                        ,('Casado', 'Casado')
                                        ,('Companero', 'Compañero de vida')]
                                        , string='Estado',default='single')
    cuenta_tipo=fields.Selection(selection=[('Ahorro', 'Ahorro')
                                        ,('Corriente', 'Corriente')]
                                        , string='Tipo de cuenta')
    cuenta_banco_id=fields.Many2one(comodel_name='res.bank', string='Banco')
    dui_image=fields.Binary("Imagen del DUI")
    nit_image=fields.Binary("Imagen del NIT")


    def compute_name(self):
        self.name = self.nombre+' '+self.apellidos


class fuente_empleado(models.Model):
    _name='fiaes.fuente_empleado'
    _description='Fuente de financiamiento por empleado'
    name= fields.Char("Fuente")
    proyecto_id=fields.Many2one(comodel_name='project.project', string='Proyecto')
    fuente_id=fields.Many2one(comodel_name='fiaes.fuente', string='Fuente')
    contrato_id=fields.Many2one(comodel_name='hr.contract', string='Contrato')
    porcentaje=fields.Float("% del salario",digits=(20,10))


class contrato(models.Model):
    _inherit = 'hr.contract'
    sueldo_dia= fields.Float("Sueldo por dia",compute='compute_salario',digits=(20,8))
    sueldo_hora=fields.Float("Sueldo por hora",compute='compute_salario',digits=(20,8))
    sueldo_minuto=fields.Float("Sueldo por minuto",compute='compute_salario',digits=(20,8))
    fuente_ids=fields.One2many('fiaes.fuente_empleado','contrato_id', 'Fuentes')

    @api.one
    @api.depends('wage')
    def compute_salario(self):
        for record in self:
            record.sueldo_dia=record.wage/30.00
            record.sueldo_hora=record.sueldo_dia/8.00
            record.sueldo_minuto=record.sueldo_hora/60.00

class telefono(models.Model):
    _name = 'fiaes.telefono'
    _description= 'Solicitud de vehiculo'
    name=fields.Char("Tipo de telefono")
    telefono=fields.Char("Phone")
    contacto_id=fields.Many2one(comodel_name='res.partner', string='Contacto')

class contacto(models.Model):
    _inherit = 'res.partner'
    nombres=fields.Char("Nombres")
    apellidos=fields.Char("Apellidos")
    nombre_comercial=fields.Char("Nombre comercial")
    nit=fields.Char("NIT")
    nrc=fields.Char("NRC")
    departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento')
    municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio')
    representante_nombre=fields.Char("Representante legal")
    representante_nit=fields.Char("NIT del representante")
    representante_dui=fields.Char("NRC del representante")
    representante_nacionalidad=fields.Many2one(comodel_name='res.country', string='Nacionalidad del representante')
    representante_nacimiento=fields.Date("Fecha de nacimiento del representante legal")
    representante_profesion=fields.Char("Profesion del representante legal")
    contacto=fields.Char("Contacto")
    contacto_email=fields.Char("Email del contacto")
    giro=fields.Char("Giro")
    telefono_ids=fields.One2many('fiaes.telefono','contacto_id', 'Telefono')
    nit_image=fields.Binary("Imagen del NIT Sociedad")
    dui_rep_image=fields.Binary("Imagen del DUI del representante legal")
    nit_rep_image=fields.Binary("Imagen del NIT del representante legal")
    tipo=fields.Selection(selection=[('Aliado', 'Aliado')
                                        ,('Donante', 'Donante')
                                        ,('Titular', 'Titular')
                                        ,('Proveedor', 'Proveedor')
                                        ,('Ejecutora', 'Ejecutora')]
                                        , string='Tipo de solicitante')
    usuario_id=fields.Many2one(comodel_name='res.users', string='Usuario asociado')
    employee_id=fields.Many2one(comodel_name='hr.employee', string='Enlace')
    tipo_titular=fields.Selection(selection=[('Sociedad', 'Sociedad')
                                    ,('ONG', 'ONG, Adesco, Microregione y Cooperativa')
                                    ,('Gobierno', 'Entidad Pública')
                                    ,('Persona', 'Persona Natural')]
                                    , string='Tipo',required=True,default='Sociedad',track_visibility=True)




class red(models.Model):
    _name='fiaes.red'
    _description='Redes'
    tipo=fields.Selection(selection=[('Contacto', 'Contacto')
                                        ,('Otro', 'Otro')]
                                        , string='Tipo',default='Contacto')
    otro=fields.Char("Nombre")
    name=fields.Char(string='Nombre',compute='get_nombre')
    partner_id=fields.Many2one(comodel_name='res.partner', string='Contacto')
    abreviatura=fields.Char("Abreviatura")
    alcance=fields.Selection(selection=[('Nacional', 'Nacional')
                                        ,('Regional', 'Regional')
                                        ,('Mundial', 'Mundial')]
                                        , string='Alcance',default='Nacional')
    puntofocal=fields.Char("Punto focal")
    contacto=fields.Char("Nombre del contacto del punto focal")
    correo=fields.Char("Correo electronico")
    telefono=fields.Char("Telefono")
    direccion=fields.Char("Direccion")
    miembros=fields.Many2many(comodel_name='res.partner', string='Miembros')
    sede=fields.Many2one(comodel_name='res.country', string='Sede')
    estado=fields.Selection(selection=[('Acreditado', 'Acreditado')
                                        ,('No Acreditado', 'No Acreditado')
                                        ,('En proceso', 'En proceso de acreditación')]
                                        , string='Estado',default='No Acreditado')
    @api.one
    @api.depends('tipo','otro','partner_id')
    def get_nombre(self):
        for record in self:
            if record.tipo=='Contacto':
                if record.partner_id:
                    record.name=record.partner_id.name
            else:
                if record.otro:
                    record.name=record.otro


#Proyecto institucional
class proyecto_institucional(models.Model):
    _inherit='project.project'
    codigo=fields.Char("Codigo")
    tipo=fields.Selection(selection=[('Institucional', 'Proyecto Institucional')
                                        ,('Administrado', 'Administrado')]
                                        , string='Tipo de Proyecto',default='Institucional')
    fuente_ids=fields.Many2many(comodel_name='fiaes.fuente', relation='proyecto_fuente_rel',string='Fuentes')
    contacto_ids=fields.Many2many(comodel_name='res.partner', relation='proyecto_contacto_rel', string='Contactos')
    responsable_ids=fields.Many2many(comodel_name='res.partner', relation='proyecto_responsable_rel', string='Responsable')
    cordenada_ids=fields.One2many('fiaes.proyecto_cordenadas','proyecto_id', 'Cordenadas')
    objetivo_ids=fields.One2many('fiaes.proyecto_objetivo','proyecto_id', 'Objetivos especificos')
    territorio_id=fields.Many2one(comodel_name='fiaes.territorio', string='Territorio')
    objetivo=fields.Text("Objetivo General")
    state=fields.Selection(selection=[('Enproceso', 'En Proceso')
                                        ,('Abierto', 'Abierto')
                                        ,('Cerrado', 'Cerrado')]
                                        , string='Estado del proyecto',default='Enproceso')
    @api.one
    def abrir(self):
        for r in self:
            r.state='Abierto'
    
    @api.one
    def cerrar(self):
        for r in self:
            r.state='Cerrado'

class proyecto_objetivo(models.Model):
    _name = "fiaes.proyecto_objetivo"
    _description = "Objetivos especificos"
    name = fields.Char('Obetivo')
    proyecto_id=fields.Many2one(comodel_name='project.project', string='Proyecto')




class proyecto_cordenadas(models.Model):
    _name = "fiaes.proyecto_cordenadas"
    _description = "Cordenadas donde se desarrolla el proyecto"
    name = fields.Char('Descripcion')
    coordenadas_latitud=fields.Float("Latitud",digits=(20,7))
    coordenadas_longitud=fields.Float("Longitud",digits=(20,7))
    proyecto_id=fields.Many2one(comodel_name='project.project', string='Proyecto')

class task_institucional(models.Model):
    _inherit='project.task'
    codigo=fields.Char("Codigo")
    objetivo_id=fields.Many2one(comodel_name='fiaes.proyecto_objetivo', string='Objetivo')
    tipo=fields.Selection(selection=[('Institucional', 'Proyecto Institucional')
                                        ,('Administrado', 'Administrado')]
                                        , string='Tipo de Proyecto',related="project_id.tipo")
    responsable_ids=fields.Many2many(comodel_name='res.partner', relation='task_responsable_rel', string='Responsables')
    cordinacion_ids=fields.Many2many(comodel_name='res.partner', relation='task_cordinacion_rel', string='En coordinacion')
    inicio=fields.Date("Fecha de inicio")
    fin=fields.Date("Fecha de fin")
    cordenada_ids=fields.One2many('fiaes.task_cordenadas','task_id', 'Cordenadas')
    recurso_ids=fields.One2many('fiaes.task_recurso','task_id', 'Recursos')

class task_cordenadas(models.Model):
    _name = "fiaes.task_cordenadas"
    _description = "Cordenadas donde se desarrolla el proyecto"
    name = fields.Char('Descripcion')
    coordenadas_latitud=fields.Float("Latitud",digits=(20,7))
    coordenadas_longitud=fields.Float("Longitud",digits=(20,7))
    task_id=fields.Many2one(comodel_name='project.task', string='Actividad')

class task_recursos(models.Model):
    _name = "fiaes.task_recurso"
    _description = "Recursos institucionales"
    name = fields.Char('Nombre')
    cantidad=fields.Float("Cantidad",digits=(20,3))
    descripcion = fields.Char('Descripcion')
    account_id=fields.Many2one(comodel_name='account.account', string='Cuenta asociada')
    valor=fields.Float("Valor estimado",digits=(20,3))
    task_id=fields.Many2one(comodel_name='project.task', string='Actividad')
    tipo=fields.Selection(selection=[('Institucional', 'Proyecto Institucional')
                                        ,('Administrado', 'Administrado')]
                                        , string='Tipo de Proyecto',related="task_id.tipo")


class unidad(models.Model):
    _inherit='hr.department'
    codigo=fields.Char("Codigo")



class territorio_cordenadas(models.Model):
    _name = "fiaes.territorio_cordenadas"
    _description = "Cordenadas del poligo que define a cada rerritorio"
    name = fields.Char('Descripcion')
    coordenadas_latitud=fields.Float("Latitud",digits=(20,7))
    coordenadas_longitud=fields.Float("Longitud",digits=(20,7))
    territorio_id=fields.Many2one(comodel_name='fiaes.territorio', string='Territorio')


class territorio(models.Model):
    _name = "fiaes.territorio"
    _inherit= ['mail.thread']
    _description = "Territorios"
    codigo = fields.Char('Codigo',track_visibility=True)
    name = fields.Char('Territorio',track_visibility=True)
    codigo = fields.Char('Codigo',track_visibility=True)
    descripcion=fields.Text("Descripcion",track_visibility=True)
    cordenada_ids=fields.One2many('fiaes.territorio_cordenadas','territorio_id', 'Cordenadas',track_visibility=True)
    contacto_ids=fields.Many2many(comodel_name='res.partner', relation='territorio_contacto_rel', string='Contactos',track_visibility=True)
    responsable_ids=fields.Many2many(comodel_name='hr.employee', relation='territorio_responsable_rel', string='Responsable',track_visibility=True)
    unidades_ids=fields.Many2many(comodel_name='hr.department', relation='territorio_deparment_rel', string='Unidades',track_visibility=True)


class bank(models.Model):
    _inherit = 'res.bank'
    abba= fields.Char("ABBA")
    bank_id=fields.Many2one(comodel_name='res.bank', string='Banco intermediario')
    cuenta_intermedio=fields.Char("Cuenta de intermediacion")
