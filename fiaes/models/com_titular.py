# -*- coding: utf-8 -*-
##############################################################################

import uuid
#from . import numero_letras
from odoo import api, models, fields, _
from datetime import datetime, timedelta,date
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__) 
#from numero_letras import numero_a_letras, numero_a_moneda





def numero_to_letras(numero):
    indicador = [("",""),("MIL","MIL"),("MILLON","MILLONES"),("MIL","MIL"),("BILLON","BILLONES")]
    entero = int(numero)
    decimal = int(round((numero - entero)*100))
    #print 'decimal : ',decimal 
    contador = 0
    numero_letras = ""
    _logger.info('ENTERO:'+str(entero))
    while entero >0:
        a = entero % 1000
        if contador == 0:
            en_letras = convierte_cifra(a,1).strip()
            _logger.info('letras 1:'+en_letras)
        else :
            en_letras = convierte_cifra(a,0).strip()
            _logger.info('letras 2:'+en_letras)
        if a==0:
            numero_letras = en_letras+" "+numero_letras
            _logger.info('letras 3:'+numero_letras)
        elif a==1:
            if contador in (1,3):
                numero_letras = indicador[contador][0]+" "+numero_letras
                _logger.info('letras 4:'+numero_letras)
            else:
                numero_letras = en_letras+" "+indicador[contador][0]+" "+numero_letras
                _logger.info('letras 5:'+numero_letras)
        else:
            numero_letras = en_letras+" "+indicador[contador][1]+" "+numero_letras
            _logger.info('letras 6:'+numero_letras)
        numero_letras = numero_letras.strip()
        contador = contador + 1
        entero = int(entero / 1000)
    numero_letras = numero_letras+" CON " + str(decimal) +"/100"
    return numero_letras
 

def convierte_cifra(numero,sw):
    lista_centana = ["",("CIEN","CIENTO"),"DOSCIENTOS","TRESCIENTOS","CUATROCIENTOS","QUINIENTOS","SEISCIENTOS","SETECIENTOS","OCHOCIENTOS","NOVECIENTOS"]
    lista_decena = ["",("DIEZ","ONCE","DOCE","TRECE","CATORCE","QUINCE","DIECISEIS","DIECISIETE","DIECIOCHO","DIECINUEVE"),
                    ("VEINTE","VEINTI"),("TREINTA","TREINTA Y "),("CUARENTA" , "CUARENTA Y "),
                    ("CINCUENTA" , "CINCUENTA Y "),("SESENTA" , "SESENTA Y "),
                    ("SETENTA" , "SETENTA Y "),("OCHENTA" , "OCHENTA Y "),
                    ("NOVENTA" , "NOVENTA Y ")
                ]
    lista_unidad = ["",("UN" , "UNO"),"DOS","TRES","CUATRO","CINCO","SEIS","SIETE","OCHO","NUEVE"]
    centena = int (numero / 100)
    decena = int((numero -(centena * 100))/10)
    unidad = int(numero - (centena * 100 + decena * 10))
    #print "centena: ",centena, "decena: ",decena,'unidad: ',unidad
    texto_centena = ""
    texto_decena = ""
    texto_unidad = ""
    #Validad las centenas
    texto_centena = lista_centana[centena]
    if centena == 1:
        if (decena + unidad)!=0:
            texto_centena = texto_centena[1]
        else :
            texto_centena = texto_centena[0]
    #Valida las decenas
    texto_decena = lista_decena[decena]
    if decena == 1 :
         texto_decena = texto_decena[unidad]
    elif decena > 1 :
        if unidad != 0 :
            texto_decena = texto_decena[1]
        else:
            texto_decena = texto_decena[0]
    #Validar las unidades
    #print "texto_unidad: ",texto_unidad
    if decena != 1:
        texto_unidad = lista_unidad[unidad]
        if unidad == 1:
            texto_unidad = texto_unidad[sw]
    return "%s %s %s" %(texto_centena,texto_decena,texto_unidad)


def calculo_letras(campo):
    cadena = list(campo)
    a = []
    for record in cadena: 
        if record=='0':
            a.append('cero')
        if record=='1':
            a.append('uno')
        if record=='2':
            a.append('dos')
        if record=='3':
            a.append('tres')
        if record=='4':
            a.append('cuatro')
        if record=='5':
            a.append('cinco')
        if record=='6':
            a.append('seis')
        if record=='7':
            a.append('siete')
        if record=='8':
            a.append('ocho')
        if record=='9':
            a.append('nueve')
        if record=='-':
            a.append('-')
            
    str1  = ' '.join(a)
    return str1

class solicitud_registro_action(models.Model):
    _name='fiaes.compensacion.action'
    name=fields.Char("Accion",related="proceso_id.name")
    proceso_id=fields.Many2one("fiaes.compensacion.proceso")
    state=fields.Selection(selection=[('Solicitud', 'Solicitudes en proceso')
                                    ,('Recibida', 'Recibida')
                                    ,('RevisionTitular', 'Revision (Datos del titular)')
                                    ,('RevisionProyecto', 'Revision (Datos del proyecto)')
                                    ,('RevisionLegal', 'Revision (Documentos legales)')
                                    ,('Aprobada', 'Solicitud Aprobada')
                                    ,('Plan', 'Plan de desembolsos y fianzas en elaboracion')
                                    ,('PlanTitular', 'Plan de desembolsos aprobado por el titular')
                                    ,('PlanAprobadoTitular', 'Plan de desembolsos aprobado por el titular')
                                    ,('Convenio', 'Convenio en elaboracion')
                                    ,('ConvenioTitular', 'Convenio en revision titular')
                                    ,('ConvenioAprobadoTitular', 'Convenio aprobado por el titular')
                                    ,('ConvenioMarn', 'Convenio en revision MARN')
                                    ,('ConvenioAprobadoMarn', 'Convenio aprobado por el MARN')
                                    ,('RevisionPago', 'Revision de pago y fianza')
                                    ,('FirmaProgramada', 'Programacion de firma de convenio')
                                    ,('Firmado', 'Convenio Firmado')
                                    ,('NoAprobada', 'No Aprobar')]
                                    , string='Estado',required=True,default='Solicitud',track_visibility=True)
    comentario=fields.Char("Comentario")
    
    @api.model
    def create(self, values):
        # Override the original create function for the res.partner model
        record = super(solicitud_registro_action, self).create(values)
        proceso=self.env['fiaes.compensacion.proceso'].search([('id','=',record.proceso_id.id)],limit=1)
        if proceso:
            proceso.state=record.state
            if record.comentario:
                 self.message_post(body=record.comentario)
        return record
    

class solicitud_registro_solicitud(models.Model):
    _name='fiaes.compensacion.solicitud'
    _inherit= ['mail.thread']
    _description= 'Solicitud de registro de titular'
    name=fields.Char("Razon social")
    nombre_comercial=fields.Char("Nombre comercial o abreviatura")
    representante_legal=fields.Char("Representante legal")
    empresa_nit=fields.Char("NIT de la empresa")
    representante_nit=fields.Char("NIT del representante legal")
    representante_dui=fields.Char("DUI del representante legal")
    apoderado=fields.Char("Apoderado")
    apoderado_nit=fields.Char("NIT del apoderado")
    apoderado_dui=fields.Char("DUI del apoderado")
    poder=fields.Binary("Poder General Administrativo o equivalente")
    poder_filename=fields.Char("Poder file name")
    departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento donde esta la empresa')
    municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio donde esta la empresa')
    representante_nacionalidad=fields.Many2one(comodel_name='res.country', string='Nacionalidad del representante')
    representante_profesion=fields.Char("Profesion del representante")
    representante_nacimeinto=fields.Date("Fecha de nacimiento del representante legal")
    contacto=fields.Char("Contacto de la empresa")
    contacto_email=fields.Char("Email del contacto")
    usuario_id=fields.Many2one(comodel_name='res.users', string='Usuario asociado')
    tipo=fields.Selection(selection=[('Sociedad', 'Sociedad')
                                    ,('ONG', 'ONG, Adesco, Microregione y Cooperativa')
                                    ,('Gobierno', 'Entidad Pública')
                                    ,('Persona', 'Persona Natural')]
                                    , string='Tipo',required=True,default='Sociedad',track_visibility=True)
    #INFORMACION DEL PROYECTO
    proyecto_name=fields.Char("Proyecto")
    proyecto_descripcion=fields.Text("Descripcion")
    proyecto_resolucion=fields.Char("Numero de resolucion")
    proyecto_resolucion_nfa=fields.Char("NFA Correlativo")
    proyecto_resolucion_fecha=fields.Date("Fecha de resolucion")
    proyecto_direccion=fields.Char("Direccion del proyecto")
    proyecto_departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento donde esta la empresa')
    proyecto_municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio donde esta la empresa')
    proyecto_afectacion=fields.Text("Descripción de la afectación del proyecto")
    proyecto_vencimiento=fields.Date("Vencimiento")
    proyecto_valor=fields.Float("Valor de la compensación")
    proyecto_valor_letras=fields.Char("Valor de la compensación en letras",compute='fill_letras')
    proyecto_resolucion_file=fields.Binary('Resolución',help='Resolución')
    #INFORMACION LEGAL
    legal_escritura=fields.Binary('Escritura Pública de constitución',help='Inscrita en el registro de comercio')
    legal_modificacion=fields.Binary('Documento de modificación, rectificación, transformación o fusión de la entidad',help='Inscrita en el registro de comercio')
    legal_credencial=fields.Binary('Credencial de Junta Directiva o del Representante Legal',help='Inscrita en el registro de comercio')
    legal_renovacion=fields.Binary('Constancia de renovación de matrícula de empresa vigente',help='Recibo de pago, constancia del trámite de emisión o renovación de matrícula')
    legal_representante_dui=fields.Binary('DUI/Pasaporte/Carnet de residente del Representante Legal',help='Vigente')
    legal_representante_nit=fields.Binary('NIT del Representante Legal',help='NIT del Representante Legal')
    legal_sociedad_nit=fields.Binary('NIT de la sociedad',help='NIT de la sociedad')
    legal_iva=fields.Binary('IVA - Registro de contribuyente',help='Vigente')
    legal_certificacion=fields.Binary('Certificación del punto de acta de autorización del Representante Legal ',help='Para firmar el convenio de compensación ambiental, otorgar garantías, realizar diligencias necesarias, y firmar documentos para dicho fín. Documento legalizado por un notario')
    legal_poder=fields.Binary('Poder a nombre de la persona natural que se faculta para la firma y representación',help='Sólo si es apoderado. ')
    legal_apoderado_dui=fields.Binary('DUI/Pasaporte/Carnet de residente del Apoderado',help='Vigente')
    legal_apoderado_nit=fields.Binary('NIT del apoderado',help='Vigente')
    legal_estatutos=fields.Binary('Copia de la parte completa de los Estatutos vigentes publicados en el Diario Oficial ',help='Vigente')
    legal_ley_creacion=fields.Binary('Ley de creación de la entidad',help='Ley de creación de la entidad')
    legal_representante_diario=fields.Binary('Publicación del Diario Oficial del Acuerdo de nombramiento del Representante Legal ',help='Publicación del Diario Oficial del Acuerdo de nombramiento del Representante Legal ')
    legal_persona_dui=fields.Binary('DUI/Pasaporte/Carnet de residente de la persona natural',help='Vigente')
    legal_persona_nit=fields.Binary('NIT de la persona natural',help='Vigente')
    procesar=fields.Boolean("Procesar esta solicitud, si no se marca solo se guardar")
    proceso_uuid=fields.Char("UUID del proceso")
    
    
    @api.one
    @api.depends('proyecto_valor')
    def fill_letras(self):
        for r in self:
            r.proyecto_valor_letras=numero_to_letras(r.proyecto_valor)
    
    @api.model
    def create(self, values):
        # Override the original create function for the res.partner model
        record = super(solicitud_registro_solicitud, self).create(values)
        #enviando el correo de confirmacion
        if not record.proceso_uuid:
            record.proceso_uuid=uuid.uuid4().hex
            values['proceso_uuid']=record.proceso_uuid
        else:
            prev=self.env['fiaes.compensacion.solicitud'].search([('proceso_uuid','=',record.proceso_uuid),('id','!=',record.id)],limit=1)
            if prev:
                if not record.legal_escritura:
                    record.legal_escritura=prev.legal_escritura
                if not record.legal_modificacion:
                    record.legal_modificacion=prev.legal_modificacion
                if not record.legal_credencial:
                    record.legal_credencial=prev.legal_credencial
                if not record.legal_renovacion:
                    record.legal_renovacion=prev.legal_renovacion
                if not record.legal_representante_dui:
                    record.legal_representante_dui=prev.legal_representante_dui
                if not record.legal_representante_nit:
                    record.legal_representante_nit=prev.legal_representante_nit
                if not record.legal_sociedad_nit:
                    record.legal_sociedad_nit=prev.legal_sociedad_nit
                if not record.legal_iva:
                    record.legal_iva=prev.legal_iva
                if not record.legal_certificacion:
                    record.legal_certificacion=prev.legal_certificacion
                if not record.legal_poder:
                    record.legal_poder=prev.legal_poder
                if not record.legal_apoderado_dui:
                    record.legal_apoderado_dui=prev.legal_apoderado_dui
                if not record.legal_apoderado_nit:
                    record.legal_apoderado_nit=prev.legal_apoderado_nit
                if not record.legal_ley_creacion:
                    record.legal_ley_creacion=prev.legal_ley_creacion
                if not record.legal_representante_diario:
                    record.legal_representante_diario=prev.legal_representante_diario
                if not record.legal_persona_dui:
                    record.legal_persona_dui=prev.legal_persona_dui
                if not record.legal_persona_nit:
                    record.legal_persona_nit=prev.legal_persona_nit
                if not record.poder:
                    record.poder=prev.poder
            self.env['fiaes.compensacion.solicitud'].search([('proceso_uuid','=',record.proceso_uuid),('id','!=',record.id)]).unlink()
        if record.procesar:
            values['state']='Solicitud'
            proceso=self.env['fiaes.compensacion.proceso'].create(values)
            if proceso:
                if not proceso.legal_escritura:
                    proceso.legal_escritura=record.legal_escritura
                if not proceso.legal_modificacion:
                    proceso.legal_modificacion=record.legal_modificacion
                if not proceso.legal_credencial:
                    proceso.legal_credencial=record.legal_credencial
                if not proceso.legal_renovacion:
                    proceso.legal_renovacion=record.legal_renovacion
                if not proceso.legal_representante_dui:
                    proceso.legal_representante_dui=record.legal_representante_dui
                if not proceso.legal_representante_nit:
                    proceso.legal_representante_nit=record.legal_representante_nit
                if not proceso.legal_sociedad_nit:
                    proceso.legal_sociedad_nit=record.legal_sociedad_nit
                if not proceso.legal_iva:
                    proceso.legal_iva=record.legal_iva
                if not proceso.legal_certificacion:
                    proceso.legal_certificacion=record.legal_certificacion
                if not proceso.legal_poder:
                    proceso.legal_poder=record.legal_poder
                if not proceso.legal_apoderado_dui:
                    proceso.legal_apoderado_dui=record.legal_apoderado_dui
                if not proceso.legal_apoderado_nit:
                    proceso.legal_apoderado_nit=record.legal_apoderado_nit
                if not proceso.legal_ley_creacion:
                    proceso.legal_ley_creacion=record.legal_ley_creacion
                if not proceso.legal_representante_diario:
                    proceso.legal_representante_diario=record.legal_representante_diario
                if not proceso.legal_persona_dui:
                    proceso.legal_persona_dui=record.legal_persona_dui
                if not proceso.legal_persona_nit:
                    proceso.legal_persona_nit=record.legal_persona_nit
                if not proceso.poder:
                    proceso.poder=record.poder
            template = self.env.ref('fiaes.compensacion_titular_solicitud_ingreso', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(proceso.id)
        return record
    
    
    

class solicitud_registro_proceso(models.Model):
    _name='fiaes.compensacion.proceso'
    _inherit= ['mail.thread','mail.activity.mixin']
    _description= 'Solicitud de registro de titular'
    name=fields.Char("Razon social")
    nombre_comercial=fields.Char("Nombre comercial o abreviatura")
    representante_legal=fields.Char("Representante legal")
    empresa_nit=fields.Char("NIT de la empresa")
    empresa_nit_letras=fields.Char("NIT de la empresa",compute='getletras')
    representante_nit=fields.Char("NIT del representante legal")
    representante_nit_letras=fields.Char("NIT del representante legal",compute='getletras1')
    representante_dui=fields.Char("DUI del representante legal")
    representante_dui_letras=fields.Char("DUI del representante legal",compute='getletras2')
    apoderado=fields.Char("Apoderado")
    apoderado_nit=fields.Char("NIT del apoderado")
    apoderado_nit_letras=fields.Char("NIT del apoderado",compute='getletras3')
    apoderado_dui=fields.Char("DUI del apoderado")
    apoderado_dui_letras=fields.Char("DUI del apoderado",compute='getletras4')
    poder=fields.Binary("Poder General Administrativo o equivalente")
    poder_filename=fields.Char("Poder file name")
    departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento donde esta la empresa')
    municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio donde esta la empresa')
    representante_nacionalidad=fields.Many2one(comodel_name='res.country', string='Nacionalidad del representante')
    representante_profesion=fields.Char("Profesion del representante")
    representante_nacimeinto=fields.Date("Fecha de nacimiento del representante legal")
    contacto=fields.Char("Contacto de la empresa")
    contacto_email=fields.Char("Email del contacto")
    state=fields.Selection(selection=[('Solicitud', 'Solicitudes en proceso')
                                    ,('Recibida', 'Recibida')
                                    ,('RevisionTitular', 'Revision (Datos del titular)')
                                    ,('RevisionProyecto', 'Revision (Datos del proyecto)')
                                    ,('RevisionLegal', 'Revision (Documentos legales)')
                                    ,('Aprobada', 'Solicitud Aprobada')
                                    ,('Plan', 'Plan de desembolsos y fianzas en elaboracion')
                                    ,('PlanTitular', 'Plan de desembolsos aprobado por el titular')
                                    ,('PlanAprobadoTitular', 'Plan de desembolsos aprobado por el titular')
                                    ,('Convenio', 'Convenio en elaboracion')
                                    ,('ConvenioTitular', 'Convenio en revision titular')
                                    ,('ConvenioAprobadoTitular', 'Convenio aprobado por el titular')
                                    ,('ConvenioMarn', 'Convenio en revision MARN')
                                    ,('ConvenioAprobadoMarn', 'Convenio aprobado por el MARN')
                                    ,('RevisionPago', 'Revision de pago y fianza')
                                    ,('FirmaProgramada', 'Programacion de firma de convenio')
                                    ,('Firmado', 'Convenio Firmado')
                                    ,('NoAprobada', 'No Aprobar')]
                                    , string='Estado',required=True,default='Solicitud',track_visibility=True)
    state_avance=fields.Integer('avance')
    usuario_id=fields.Many2one(comodel_name='res.users', string='Usuario asociado')
    tipo=fields.Selection(selection=[('Sociedad', 'Sociedad')
                                    ,('ONG', 'ONG, Adesco, Microregione y Cooperativa')
                                    ,('Gobierno', 'Entidad Pública')
                                    ,('Persona', 'Persona Natural')]
                                    , string='Tipo',required=True,default='Sociedad',track_visibility=True)
    #INFORMACION DEL PROYECTO
    proyecto_name=fields.Char("Proyecto")
    proyecto_descripcion=fields.Text("Descripcion")
    proyecto_resolucion=fields.Char("Numero de resolucion")
    proyecto_resolucion_nfa=fields.Char("NFA Correlativo")
    proyecto_resolucion_fecha=fields.Date("Fecha de resolucion")
    proyecto_direccion=fields.Char("Direccion del proyecto")
    proyecto_departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento donde esta el proyecto')
    proyecto_municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio donde esta el proyecto')
    proyecto_afectacion=fields.Text("Descripción de la afectación del proyecto")
    proyecto_vencimiento=fields.Date("Vencimiento")
    proyecto_valor=fields.Float("Valor de la compensación")
    proyecto_valor_letras=fields.Char("Valor de la compensación en letras",compute='fill_letras')
    proyecto_resolucion_file=fields.Binary('Resolución',help='Resolución')
    #INFORMACION LEGAL
    legal_escritura=fields.Binary('Escritura Pública de constitución',help='Inscrita en el registro de comercio')
    legal_modificacion=fields.Binary('Documento de modificación, rectificación, transformación o fusión de la entidad',help='Inscrita en el registro de comercio')
    legal_credencial=fields.Binary('Credencial de Junta Directiva o del Representante Legal',help='Inscrita en el registro de comercio')
    legal_renovacion=fields.Binary('Constancia de renovación de matrícula de empresa vigente',help='Recibo de pago, constancia del trámite de emisión o renovación de matrícula')
    legal_representante_dui=fields.Binary('DUI/Pasaporte/Carnet de residente del Representante Legal',help='Vigente')
    legal_representante_nit=fields.Binary('NIT del Representante Legal',help='NIT del Representante Legal')
    legal_sociedad_nit=fields.Binary('NIT de la sociedad',help='NIT de la sociedad')
    legal_iva=fields.Binary('IVA - Registro de contribuyente',help='Vigente')
    legal_certificacion=fields.Binary('Certificación del punto de acta de autorización del Representante Legal ',help='Para firmar el convenio de compensación ambiental, otorgar garantías, realizar diligencias necesarias, y firmar documentos para dicho fín. Documento legalizado por un notario')
    legal_poder=fields.Binary('Poder a nombre de la persona natural que se faculta para la firma y representación',help='Sólo si es apoderado. ')
    legal_apoderado_dui=fields.Binary('DUI/Pasaporte/Carnet de residente del Apoderado',help='Vigente')
    legal_apoderado_nit=fields.Binary('NIT del apoderado',help='Vigente')
    
    legal_estatutos=fields.Binary('Copia de la parte completa de los Estatutos vigentes publicados en el Diario Oficial ',help='Vigente')
    
    legal_ley_creacion=fields.Binary('Ley de creación de la entidad',help='Ley de creación de la entidad')
    legal_representante_diario=fields.Binary('Publicación del Diario Oficial del Acuerdo de nombramiento del Representante Legal ',help='Publicación del Diario Oficial del Acuerdo de nombramiento del Representante Legal ')
    
    legal_persona_dui=fields.Binary('DUI/Pasaporte/Carnet de residente de la persona natural',help='Vigente')
    legal_persona_nit=fields.Binary('NIT de la persona natural',help='Vigente')
    proceso_uuid=fields.Char("UUID del proceso")
    titular_id=fields.Many2one(comodel_name='res.partner', string='Titular')
    proyecto_id=fields.Many2one(comodel_name='fiaes.compensacion.proyecto', string='Proyecto')
    comentario_plan=fields.Text("Comentarios al plan")
    comentario_convenio=fields.Text("Comentarios al convenio")
    fecha_actual = fields.Date("Fecha",compute='actual')
    x_fecha = fields.Char("Fecha letras", compute='fechas')
    
    @api.one
    def actual(self):
        for r in self:
            day = date.today()
            r.fecha_actual = day
    
    @api.one
    @api.depends('fecha_actual')
    def fechas(self):
        for r in self:
            anio = r.fecha_actual.year
            aniofecha = str(anio)
            months = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
            days =("uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve","diez","once","doce","trece","catorce","quince","diesciseis","diecisiete","dieciocho","diecinueve","veinte","ventiuno","veintidos","veintitres","veinticuatro","veinticinco","veintiseis","veintisiete","veintiocho","veintinueve","treinta","treinta y uno")
            day = days[r.fecha_actual.day-1]
            month = months[r.fecha_actual.month -1]
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
        
    @api.one
    @api.depends('empresa_nit')
    def getletras(self):
        for r in self:            
            r.empresa_nit_letras = calculo_letras(r.empresa_nit)
            
    
    @api.one
    @api.depends('representante_nit')
    def getletras1(self):
        for r in self:            
            r.representante_nit_letras = calculo_letras(r.representante_nit)
                    
    
    @api.one
    @api.depends('representante_dui')
    def getletras2(self):
        for r in self:            
            r.representante_dui_letras = calculo_letras(r.representante_dui)   
                 
  
    @api.one
    @api.depends('apoderado_nit')
    def getletras3(self):
        for r in self:            
            r.apoderado_nit_letras = calculo_letras(r.apoderado_nit)  
            
    @api.one
    @api.depends('apoderado_nit')
    def getletras4(self):
        for r in self:            
            r.apoderado_dui_letras = calculo_letras(r.apoderado_dui)           
    
    @api.one
    @api.depends('proyecto_valor')
    def fill_letras(self):
        for r in self:
            r.proyecto_valor_letras=numero_to_letras(r.proyecto_valor)
    
    @api.model
    def create(self, values):
        # Override the original create function for the res.partner model
        record = super(solicitud_registro_proceso, self).create(values)
        #enviando el correo de confirmacion
        template = self.env.ref('fiaes.compensacion_proceso_ingreso', False)
        if template:
            self.env['mail.template'].browse(template.id).send_mail(record.id)
        return record
    
    
    @api.one
    def recibir(self):
        for r in self:
            r.state='Recibida'
            r.state_avance=2
            template = self.env.ref('fiaes.compensacion_proceso_ingreso', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    
    @api.one
    def aprobar_titular(self):
        for r in self:
            r.state='RevisionTitular'
            r.state_avance=3
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
            dict={}
            dict['name']=r.name
            dict['nombre_comercial']=r.nombre_comercial
            dict['nit']=r.empresa_nit
            dict['contacto_email']=r.contacto_email
            dict['departamento_id']=r.departamento_id.id
            dict['municipio_id']=r.municipio_id.id
            dict['representante_nombre']=r.representante_legal
            dict['representante_nit']=r.representante_nit
            dict['representante_dui']=r.representante_dui
            dict['representante_nacionalidad']=r.representante_nacionalidad.id
            dict['representante_nacimiento']=r.representante_nacimeinto
            dict['representante_profesion']=r.representante_profesion
            dict['contacto']=r.contacto
            dict['tipo']='Titular'
            dict['tipo_titular']=r.tipo
            titular=self.env['res.partner'].search([('nit','=',r.empresa_nit)],limit=1)
            if titular:
                titular.write(dict)
            else:
                titular=self.env['res.partner'].create(dict)
            r.titular_id=titular.id
    
    @api.one
    def confirmar_proyecto(self):
        for r in self:
            r.state='RevisionProyecto'
            r.state_avance=4
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
            dict={}
            dict['name']=r.proyecto_name
            dict['descripcion']=r.proyecto_descripcion
            dict['resolucion']=r.proyecto_resolucion
            dict['resolucion_nfa']=r.proyecto_resolucion_nfa
            dict['resolucion_fecha']=r.proyecto_resolucion_fecha
            dict['direccion']=r.proyecto_direccion
            dict['departamento_id']=r.proyecto_departamento_id.id
            dict['municipio_id']=r.proyecto_municipio_id.id
            dict['afectacion']=r.proyecto_afectacion
            dict['vencimiento']=r.proyecto_vencimiento
            dict['valor']=r.proyecto_valor
            dict['titular_id']=r.titular_id.id
            proyecto=self.env['fiaes.compensacion.proyecto'].create(dict)
            r.proyecto_id=proyecto.id
            
            
            
    @api.one
    def documentos_revisados(self):
        for r in self:
            r.state='RevisionLegal'
            r.state_avance=5
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    


            
    @api.one
    def rechazar(self):
        for r in self:
            r.state='Rechazado'
            r.state_avance=6
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    
    
    @api.one
    def aprobar(self):
        for r in self:
            r.state='Aprobada'
            r.state_avance=6
            #enviando el correo de confirmacion
            template = self.env.ref('fiaes.compensacion_titular_solicitud_aprobado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    
    @api.one
    def plan_elaboracion(self):
        for r in self:
            r.state='Plan'
            r.state_avance=7
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    @api.one
    def plan_titular(self):
        for r in self:
            r.state='PlanTitular'
            r.state_avance=8
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    
    @api.one
    def plan_titular_aprobado(self):
        for r in self:
            r.state='PlanAprobadoTitular'
            r.state_avance=9
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    
    
    
    @api.one
    def convenio_elaboracion(self):
        for r in self:
            r.state='Convenio'
            r.state_avance=10
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    @api.one
    def convenio_titular(self):
        for r in self:
            r.state='ConvenioTitular'
            r.state_avance=11
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    @api.one
    def convenio_titular_aprobado(self):
        for r in self:
            r.state='ConvenioAprobadoTitular'
            r.state_avance=12
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    @api.one
    def convenio_marn(self):
        for r in self:
            r.state='ConvenioMarn'
            r.state_avance=13
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    @api.one
    def convenio_marn_aprobado(self):
        for r in self:
            r.state='ConvenioAprobadoMarn'
            r.state_avance=14
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    @api.one
    def revision_pago(self):
        for r in self:
            r.state='RevisionPago'
            r.state_avance=15
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)

    @api.one
    def firma_programada(self):
        for r in self:
            r.state='FirmaProgramada'
            r.state_avance=16
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    @api.one
    def firmar(self):
        for r in self:
            r.state='Firmado'
            r.state_avance=17
            template = self.env.ref('fiaes.compensacion_proceso_estado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
                

