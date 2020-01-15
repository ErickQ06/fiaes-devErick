# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID



class proyectodesembolsoplan(models.Model):
    _name='fiaes.compensacion.desembolso.plan'
    _inherit= ['mail.thread']
    name=fields.Char("Plan",related='projecto_id.name')
    monto = fields.Float(string="Monto total",related='projecto_id.valor')
    state=fields.Selection(selection=[('Solicitado', 'Solicitado')
                                    ,('Evaluando', 'Evaluando')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Rechazado', 'Rechazado')]
                                    , string='Estado',related='projecto_id.state',required=True,default='Solicitado',track_visibility=True)
    projecto_id = fields.Many2one(comodel_name='fiaes.compensacion.proyecto',string="Proyecto")
    fase_ids=fields.One2many('fiaes.compensacion.desembolso.fase','plan_id',string='Desembolsos')
    desembolso_ids=fields.One2many('fiaes.compensacion.desembolso.desembolso','plan_id',string='Desembolsos')
    anio=fields.Integer("Año a calcular")
    
    @api.one
    def callall(self):
        hoy=date.today()
        alertas=self.env['fiaes.compensacion.desembolso.alerta'].search([('fecha','<=',datetime.strftime(hoy, '%Y-%m-%d')),('ejecutado','=',False)])
        template = self.env.ref('fiaes.compensacion_desembolso_alerta', False)
        for alerta in alertas:
            if template:
                self.env['mail.template'].browse(template.id).send_mail(alerta.id)
    
    @api.one
    def convertir_cxc(self):
        for r in self:
            anio=int(r.anio)
            for d in r.desembolso_ids:
                x=d.fecha.year;
                if x<=anio:
                    d.create_corto()
                else:
                    d.create_largo()


class proyecto_plan_fase(models.Model):
    _name='fiaes.compensacion.desembolso.fase'
    name=fields.Char("Fase")
    plan_id = fields.Many2one(comodel_name='fiaes.compensacion.desembolso.plan')
    monto = fields.Float(string="Monto")
    plazo = fields.Integer(string="Plazo(Meses)")
    frecuencia = fields.Integer(string="Frecuencia (Meses)")
    fecha1 = fields.Date(string="Fecha")
    monto1 = fields.Float(string="Monto del primer pago")
    desembolso_ids=fields.One2many('fiaes.compensacion.desembolso.desembolso','fase_id',string='Desembolsos')
    

    @api.one
    def calculofechas(self):
        for r in self:
            montodiv = r.monto-r.monto1
            totalcuota = r.plazo/r.frecuencia
            cuota = montodiv/totalcuota
            i=0
            total=montodiv
            dia=r.fecha1.day
            mes=r.fecha1.month
            anio=r.fecha1.year
            #creando el primer pago
            dict={}
            dict['name']=str('Primer pago')
            dict['fecha']=datetime.strftime(r.fecha1, '%Y-%m-%d')
            dict['monto']=r.monto1
            dict['fase_id']=r.id
            dict['fianza_monto']=r.monto
            self.env['fiaes.compensacion.desembolso.desembolso'].create(dict)
            
            while i < totalcuota:
                i=i+1
                mes=mes+r.frecuencia
                if mes>12:
                    mes=mes-12
                    anio=anio+1
                dfecha=datetime(anio, mes, dia)
                dmonto=0
                if cuota<total:
                    dmonto=cuota
                else:
                    dmonto=total
                total=total-dmonto
                dict={}
                dict['name']=str(i)
                dict['fecha']=datetime.strftime(dfecha, '%Y-%m-%d')
                dict['monto']=dmonto
                dict['fase_id']=r.id
                dict['fianza_monto']=total+dmonto
                self.env['fiaes.compensacion.desembolso.desembolso'].create(dict)
                #creando las alertas
                #alertdate=dfecha+relativedelta(months=-1)
                #self.env['fiaes.planproyecto.alertas'].create({'desembolso_id':desembolso.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
                #alertdate=dfecha+relativedelta(days=-7)
                #self.env['fiaes.planproyecto.alertas'].create({'desembolso_id':desembolso.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
                #alertdate=dfecha+relativedelta(days=7)
                #self.env['fiaes.planproyecto.alertas'].create({'desembolso_id':desembolso.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
    
    
    

class proyectoplandesembolso(models.Model):
    _name='fiaes.compensacion.desembolso.desembolso'
    _inherit= ['mail.thread']
    name = fields.Char()
    fecha= fields.Date(string="Fecha")
    fechapago= fields.Date(string="Fecha de pago")
    state=fields.Selection(selection=[('Pendiente', 'Pendiente')
                                    ,('Pagado', 'Pagado')
                                    ,('Vencido', 'Vencido')]
                                    , string='Estado',compute='compute_estado',default='Pendiente',track_visibility=True)
    monto = fields.Float(string="Monto de pago")
    fase_id = fields.Many2one(comodel_name='fiaes.compensacion.desembolso.fase')
    plan_id = fields.Many2one(comodel_name='fiaes.compensacion.desembolso.plan',related='fase_id.plan_id')
    projecto_id = fields.Many2one(comodel_name='fiaes.compensacion.proyecto',related='plan_id.projecto_id')
    calculo=fields.Char('Calculo',compute='create_alerts')
    fianza_monto=fields.Float(string="Monto de la fianza")
    fianza_plazo=fields.Integer(string="Plazo de la fianza(meses)")
    fianza_vencimiento=fields.Date(string="Vencimiento de la fianza")
    invoice_id=fields.Many2one(comodel_name='account.invoice',string="Documento CXC")
    corto_move_id=fields.Many2one(comodel_name='account.move',string="Registro contable a corto plazo")
    largo_move_id=fields.Many2one(comodel_name='account.move',string="Registro contable a largo plazo")
    #Campos relacionados
    titular_id=fields.Many2one(comodel_name='res.partner',related='projecto_id.titular_id', string='Titular',store=True)
    resolucion=fields.Char("Numero de resolucion",related='projecto_id.resolucion',store=True)
    resolucion_NFA=fields.Char("Numero de resolucion NFA",related='projecto_id.resolucion_NFA',store=True)
    resolucion_fecha=fields.Date("Fecha de resolucion",related='projecto_id.resolucion_fecha',store=True)
    departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento donde esta la empresa',related='projecto_id.departamento_id',store=True)
    municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio donde esta la empresa',related='projecto_id.municipio_id',store=True)
    
    
    
    
    #se encarga de crear la deuda a largo plazo
    def create_largo(self):
        company=self.env['res.company'].search([('id','=',1)],limit=1)
        for r in self:
            if not r.largo_move_id:
                dic={}
                dic['journal_id']=company.compensacion_journal_id.id
                dic['date']=datetime.strftime(datetime.now(), '%Y-%m-%d')
                dic['sv_concepto']='Reconocimiento de deuda:'+r.plan_id.projecto_id.titular_id.name+' '+r.plan_id.projecto_id.resolucion
                dic['partner_id']=r.plan_id.projecto_id.titular_id.id
                cargo={}
                cargo['name']='Reconocimiento de deuda:'+r.plan_id.projecto_id.titular_id.name+' '+r.plan_id.projecto_id.resolucion
                cargo['partner_id']=r.plan_id.projecto_id.titular_id.id
                cargo['account_id']=company.cargalargoplazo.id
                cargo['credit']=r.monto
                cargo['debit']=0
                abono={}
                abono['name']='Reconocimiento de deuda:'+r.plan_id.projecto_id.titular_id.name+' '+r.plan_id.projecto_id.resolucion
                abono['partner_id']=r.plan_id.projecto_id.titular_id.id
                abono['account_id']=company.abonolargoplazo.id
                abono['credit']=0
                abono['debit']=r.monto
                lines=[(0,0,abono),(0,0,cargo)]
                dic['line_ids']=lines
                move=self.env['account.move'].create(dic)
                #move.action_post()
                r.largo_move_id=move.id
    
    def create_corto(self):
        company=self.env['res.company'].search([('id','=',1)],limit=1)
        for r in self:
            if not r.corto_move_id:
                if r.largo_move_id:
                    dic={}
                    dic['journal_id']=company.compensacion_journal_id.id
                    dic['invoice_date']=datetime.strftime(datetime.now(), '%Y-%m-%d')
                    dic['sv_concepto']='Reclasificacion de deuda:'+r.plan_id.projecto_id.titular_id.name+' '+r.plan_id.projecto_id.resolucion
                    dic['partner_id']=r.plan_id.projecto_id.titular_id.id
                    dic['account_id']=company.cargacortoplazo.id
                    dic['type']='out_invoice'
                    dic['date_due']=datetime.strftime(r.fecha, '%Y-%m-%d')
                    producto={}
                    producto['name']='Reclasificacion de deuda:'+r.plan_id.projecto_id.titular_id.name+' '+r.plan_id.projecto_id.resolucion
                    producto['partner_id']=r.plan_id.projecto_id.titular_id.id
                    producto['account_id']=company.cargalargoplazo.id
                    producto['price_unit']=r.monto
                    producto['queantity']=1
                    producto['product_id']=2
                    lines=[(0,0,producto)]
                    dic['invoice_line_ids']=lines
                    invoice=self.env['account.invoice'].create(dic)
                    r.invoice_id=invoice.id
                    invoice.action_invoice_open();
                    r.corto_move_id=invoice.move_id.id
                else:
                    dic={}
                    dic['journal_id']=company.compensacion_journal_id.id
                    dic['invoice_date']=datetime.strftime(datetime.now(), '%Y-%m-%d')
                    dic['sv_concepto']='Reclasificacion de deuda:'+r.plan_id.projecto_id.titular_id.name+' '+r.plan_id.projecto_id.resolucion
                    dic['partner_id']=r.plan_id.projecto_id.titular_id.id
                    dic['account_id']=company.cargacortoplazo.id
                    dic['type']='out_invoice'
                    dic['date_due']=datetime.strftime(r.fecha, '%Y-%m-%d')
                    producto={}
                    producto['name']='Reclasificacion de deuda:'+r.plan_id.projecto_id.titular_id.name+' '+r.plan_id.projecto_id.resolucion
                    producto['partner_id']=r.plan_id.projecto_id.titular_id.id
                    producto['account_id']=company.abonarcortoplazo.id
                    producto['price_unit']=r.monto
                    producto['queantity']=1
                    producto['product_id']=2
                    lines=[(0,0,producto)]
                    dic['invoice_line_ids']=lines
                    invoice=self.env['account.invoice'].create(dic)
                    r.invoice_id=invoice.id
                    invoice.action_invoice_open();
                    r.corto_move_id=invoice.move_id.id
    @api.one
    @api.depends('fecha')
    def create_alerts(self):
        for r in self:
            self.env['fiaes.compensacion.desembolso.alerta'].search([('desembolso_id','=',r.id)]).unlink()
            alertdate=r.fecha+relativedelta(months=-1)
            self.env['fiaes.compensacion.desembolso.alerta'].create({'desembolso_id':r.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
            alertdate=r.fecha+relativedelta(days=-7)
            self.env['fiaes.compensacion.desembolso.alerta'].create({'desembolso_id':r.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
            alertdate=r.fecha+relativedelta(days=7)
            self.env['fiaes.compensacion.desembolso.alerta'].create({'desembolso_id':r.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
            r.calculo='Si'
    
    @api.one
    @api.depends('fecha','fechapago')
    def compute_estado(self):
        hoy=date.today()
        for r in self:
            if r.fechapago:
                r.state='Pagado'
            else:
                if hoy<r.fecha:
                    r.state='Pendiente'
                else:
                    r.state='Vencido'
    @api.model
    def create(self, values):
        # Override the original create function for the res.partner model
        record = super(proyectoplandesembolso, self).create(values)
        #enviando el correo de confirmacion
        #creando las alertas
        alertdate=record.fecha+relativedelta(months=-1)
        self.env['fiaes.compensacion.desembolso.alerta'].create({'desembolso_id':record.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
        alertdate=record.fecha+relativedelta(days=-7)
        self.env['fiaes.compensacion.desembolso.alerta'].create({'desembolso_id':record.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
        alertdate=record.fecha+relativedelta(days=7)
        self.env['fiaes.compensacion.desembolso.alerta'].create({'desembolso_id':record.id,'name:':'mes antes','fecha':datetime.strftime(alertdate, '%Y-%m-%d'),'Ejecutado':False})
        return record
    
    

class proyectoplanalertas(models.Model):
    _name='fiaes.compensacion.desembolso.alerta'
    name = fields.Char()
    desembolso_id = fields.Many2one(comodel_name='fiaes.compensacion.desembolso.desembolso')
    fase_id = fields.Many2one(comodel_name='fiaes.compensacion.desembolso.fase',related='desembolso_id.fase_id')
    plan_id = fields.Many2one(comodel_name='fiaes.compensacion.desembolso.plan',related='fase_id.plan_id')
    projecto_id = fields.Many2one(comodel_name='fiaes.compensacion.proyecto',string="Proyecto", related='plan_id.projecto_id')
    titular_id=fields.Many2one(comodel_name='res.partner', string='Titular',related='projecto_id.titular_id')
    usuario_id=fields.Many2one(comodel_name='res.users', string='Usuario asociado',related='titular_id.usuario_id')
    employee_id=fields.Many2one(comodel_name='hr.employee', string='Enlace',related='titular_id.employee_id')
    fecha=fields.Date(string="Fecha")
    ejecutado=fields.Boolean("Ejecutado")
    

class compensacion_conversion(models.Model):
    _name='fiaes.compensacion.conversion'
    _inherit= ['mail.thread']
    name=fields.Char("Conversion anual")
    anio=fields.Integer("Año a calcular")
    desembolso_ids=fields.One2many('fiaes.compensacion.conversion.detail','conversion_id',string='Desembolsos')
    monto_total=fields.Float("Monto total a convertir")
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Calculado', 'Calculado')
                                    ,('Procesado', 'Procesado')]
                                    , string='Estado',default='Borrador',track_visibility=True)
    
    @api.one
    def convertir_cxc(self):
        for r in self:
            anio=int(r.anio)
            r.state='Procesado'
            for d in r.desembolso_ids:
                if not d.invoice_id:
                    d.desembolso_id.create_corto()
                    d.invoice_id=d.invoice_id.id
                    d.corto_move_id=d.desembolso_id.corto_move_id
    
    @api.one
    def calcular_cxc(self):
        for r in self:
            r.state='Calculado'
            anio=int(r.anio)
            desembolsos=self.env['fiaes.compensacion.desembolso.desembolso'].search([('fecha','>=',str(anio)+'-01-01'),('fecha','<=',str(anio)+'-12-31')])
            for d in desembolsos:
                if not d.invoice_id:
                    r.monto_total=r.monto_total+d.monto
                    dic={}
                    dic['name']=d.name
                    dic['desembolso_id']=d.id
                    dic['largo_move_id']=d.largo_move_id.id
                    dic['corto_move_id']=d.corto_move_id.id
                    dic['invoice_id']=d.invoice_id.id
                    dic['conversion_id']=r.id
                    self.env['fiaes.compensacion.conversion.detail'].create(dic)




class proyectoconversiondetail(models.Model):
    _name='fiaes.compensacion.conversion.detail'
    name = fields.Char()
    desembolso_id=fields.Many2one(comodel_name='fiaes.compensacion.desembolso.desembolso',string="Desembolso")
    fecha= fields.Date(string="Fecha",related="desembolso_id.fecha")
    fechapago= fields.Date(string="Fecha de pago", related="desembolso_id.fechapago")
    state=fields.Selection(selection=[('Pendiente', 'Pendiente')
                                    ,('Pagado', 'Pagado')
                                    ,('Vencido', 'Vencido')]
                                    , string='Estado',compute='compute_estado', related="desembolso_id.state",default='Pendiente',track_visibility=True)
    monto = fields.Float(string="Monto de pago",related="desembolso_id.monto")
    fase_id = fields.Many2one(comodel_name='fiaes.compensacion.desembolso.fase',related="desembolso_id.fase_id")
    plan_id = fields.Many2one(comodel_name='fiaes.compensacion.desembolso.plan',related='fase_id.plan_id')
    invoice_id=fields.Many2one(comodel_name='account.invoice',string="Documento CXC")
    corto_move_id=fields.Many2one(comodel_name='account.move',string="Registro contable a corto plazo")
    largo_move_id=fields.Many2one(comodel_name='account.move',string="Registro contable a largo plazo")
    conversion_id=fields.Many2one(comodel_name='fiaes.compensacion.conversion',string="Conversion",ondelete='cascade')
    
    
    
class compensacion_porcentajes(models.Model):
    _name='fiaes.compensacion.calculo'
    _inherit= ['mail.thread']
    name=fields.Char("Conversion de gastos administrativos")
    anio=fields.Integer("Año a calcular")
    monto_total=fields.Float("Monto total a convertir")
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Selecionados', 'Determinar proyecto')
                                    ,('Calculado', 'Calcular')]
                                    , string='Estado',default='Borrador',track_visibility=True)
    total_poa_administrativo=fields.Float("Total administrativo en POA")
    total_poa_operativo=fields.Float("Total administrativo en POA")
    total_administrativo=fields.Float("Total administrativo",compute='sumar')
    total_operativo=fields.Float("Total administrativo",compute='sumar')
    desembolso_ids=fields.One2many('fiaes.compensacion.calculo.porcentaje','calculo_id',string='Desembolsos')
    pack_ids=fields.One2many('fiaes.compensacion.calculo.pack','calculo_id',string='Paquetes')
    porcentaje_gral_adtvo = fields.Float("% general administrativo")
    porcentaje_gral_op = fields.Float("% general operativo")


    @api.multi
    def calcular_packs(self):
        for r in self:
            r.state='Calculado'
            for p in r.desembolso_ids:
                if p.total_disponible_sg>0:
                    dic={}
                    dic['name']=p.projecto_id.name+'-'+str(r.anio)+'-'+'SG'
                    dic['projecto_id']=p.projecto_id.id
                    dic['monto']=p.total_disponible_sg
                    dic['porcentaje_administrativo']=p.porcentaje_administrativo
                    dic['porcentaje_operativo']=p.porcentaje_operativo
                    dic['monto_administrativo']=p.total_administrativo
                    dic['monto_operativo']=p.total_operativo
                    dic['fecha_disponibilidad']=str(r.anio)+'-01-01'
                    dic['calculo_id']=r.id
                    self.env['fiaes.compensacion.calculo.pack'].create(dic)
                if p.total_disponible_cg>0:
                    dic={}
                    dic['name']=p.projecto_id.name+'-'+str(r.anio)+'-'+'CG'
                    dic['projecto_id']=p.projecto_id.id
                    dic['monto']=p.total_disponible_cg
                    dic['porcentaje_administrativo']=0
                    dic['porcentaje_operativo']=0
                    dic['monto_administrativo']=0
                    dic['monto_operativo']=0
                    dic['fecha_disponibilidad']=str(r.anio)+'-01-01'
                    dic['calculo_id']=r.id
                    self.env['fiaes.compensacion.calculo.pack'].create(dic)
                if p.total_proyectado>0:
                    desembolsos=self.env['fiaes.compensacion.desembolso.desembolso'].search([('projecto_id','=',p.projecto_id.id),('fecha','>=',str(r.anio)+'-01-01'),('fecha','<=',str(r.anio)+'-12-31')])
                    for d in desembolsos:
                        dic={}
                        dic['name']=p.projecto_id.name+'-'+d.name
                        dic['projecto_id']=p.projecto_id.id
                        dic['monto']=d.monto
                        dic['porcentaje_administrativo']=p.porcentaje_administrativo
                        dic['porcentaje_operativo']=p.porcentaje_operativo
                        dic['monto_administrativo']=d.monto*p.porcentaje_administrativo
                        dic['monto_operativo']=d.monto*p.porcentaje_operativo
                        dic['fecha_disponibilidad']=d.fecha
                        dic['calculo_id']=r.id
                        self.env['fiaes.compensacion.calculo.pack'].create(dic)


    @api.multi
    def calcular_admin_general(self):
        gastos = 0.0
        for r in self:
            for p in r.desembolso_ids:
                p.porcentaje_administrativo=r.porcentaje_gral_adtvo
                
    @api.multi
    def calcular_op_general(self): 
        for r in self:
            for p in r.desembolso_ids:
                p.porcentaje_operativo = r.porcentaje_gral_op
    



    
    @api.one
    @api.depends('desembolso_ids')
    def sumar(self):
        for r in self:
            r.total_administrativo=0
            r.total_operativo=0
            for d in r.desembolso_ids:
                r.total_administrativo=r.total_administrativo+d.total_administrativo
                r.total_operativo=r.total_operativo+d.total_operativo
    
    
    @api.one
    def calcular(self):
        for r in self:
            #creando los disponibles
            r.state='Selecionados'
            proyectos=self.env['fiaes.compensacion.proyecto'].search(['|',('disponible_sin_gastos','>',0),('disponible_con_gastos','>',0)])
            for p in proyectos:
                dic={}
                dic['projecto_id']=p.id
                dic['total_disponible_sg']=p.disponible_sin_gastos
                dic['total_disponible_cg']=p.disponible_con_gastos
                dic['total_proyectado']=0
                dic['porcentaje_administrativo']=0
                dic['porcentaje_operativo']=0
                dic['total_administrativo']=0
                dic['total_operativo']=0
                dic['calculo_id']=r.id
                self.env['fiaes.compensacion.calculo.porcentaje'].create(dic)
            anio=int(r.anio)
            desembolsos=self.env['fiaes.compensacion.desembolso.desembolso'].search([('fecha','>=',str(anio)+'-01-01'),('fecha','<=',str(anio)+'-12-31')])
            for d in desembolsos:
                proyecto=self.env['fiaes.compensacion.calculo.porcentaje'].search([('projecto_id','=',d.projecto_id.id)],limit=1)
                if proyecto:
                    proyecto.total_proyectado=proyecto.total_proyectado+d.monto
                else:
                    dic2={}
                    dic2['projecto_id']=d.projecto_id.id
                    dic2['total_disponible_sg']=0
                    dic2['total_disponible_cg']=0
                    dic2['total_proyectado']=d.monto
                    dic2['porcentaje_administrativo']=0
                    dic2['porcentaje_operativo']=0
                    dic2['total_administrativo']=0
                    dic2['total_operativo']=0
                    dic2['calculo_id']=r.id
                    self.env['fiaes.compensacion.calculo.porcentaje'].create(dic2)
    
    

    
class compoensacion_porcentajes(models.Model):
    _name='fiaes.compensacion.calculo.porcentaje'
    name = fields.Char()
    projecto_id = fields.Many2one(comodel_name='fiaes.compensacion.proyecto',string="Proyecto")
    titular_id=fields.Many2one(comodel_name='res.partner',related='projecto_id.titular_id', string='Titular')
    total_disponible_sg=fields.Float("Total disponible sin gastos")
    total_disponible_cg=fields.Float("Total disponible con gastos")
    total_proyectado=fields.Float("Total proyectado")
    porcentaje_administrativo=fields.Float("% Administrativo")
    porcentaje_operativo=fields.Float("% Operativo")
    total_administrativo=fields.Float("Gastos administrativo",compute='compute_total')
    total_operativo=fields.Float("Gastos operativos",compute='compute_total')
    calculo_id=fields.Many2one(comodel_name='fiaes.compensacion.calculo',string="Conversion",ondelete='cascade')


###################################################################################################

    @api.one


    @api.one
    @api.depends('total_disponible_sg','total_proyectado','porcentaje_administrativo','porcentaje_operativo')
    def compute_total(self):
        for r in self:
            r.total_administrativo=(r.total_disponible_sg+r.total_proyectado)*(r.porcentaje_administrativo)/100
            r.total_operativo=(r.total_disponible_sg+r.total_proyectado)*(r.porcentaje_operativo)/100


####################################################################################################





class fiaesmoneypack(models.Model):
    _name='fiaes.compensacion.calculo.pack'
    _inherit= ['mail.thread']
    _description= 'Paquete de compensacion '
    name=fields.Char("Paquete de compensacion")
    projecto_id=fields.Many2one(comodel_name='fiaes.compensacion.proyecto',string="Proyecto")
    titular_id=fields.Many2one(comodel_name='res.partner',related='projecto_id.titular_id', string='Titular')
    monto=fields.Float("Monto")
    porcentaje_administrativo=fields.Float("% Administrativo")
    porcentaje_operativo=fields.Float("% Operativo")
    monto_administrativo=fields.Float("Monto de gastos administrativo",compute="calcular_inversion")
    monto_operativo=fields.Float("Monto de gastos operativos",compute="calcular_inversion")
    monto_ejecutora=fields.Float("Monto de inversion",compute="calcular_inversion")
    fecha_disponibilidad=fields.Date("Fecha de disponibilidad")
    disponible_administrativo=fields.Float("Monto disponible de gastos administrativo",compute="calcular_disponibles")
    disponible_operativo=fields.Float("Monto disponible de gastos operativos",compute="calcular_disponibles")
    disponible_ejecutora=fields.Float("Monto disponible de inversion",compute="calcular_disponibles")
    line_ids=fields.One2many('fiaes.compensacion.pack.proyecto','pack_id',string='Desembolsos por proyecto')
    subline_ids=fields.One2many('fiaes.compensacion.pack.proyecto.desembolso','pack_id',string='Desembolsos por proyecto y pago')
    calculo_id=fields.Many2one(comodel_name='fiaes.compensacion.calculo',string="Calculo")
    anio=fields.Integer("Año a calcular",related="calculo_id.anio")
    


    
    
    @api.depends('monto','porcentaje_administrativo','porcentaje_operativo')
    def calcular_inversion(self):
        for r in self:
            r.monto_administrativo=r.monto*r.porcentaje_administrativo/100
            r.monto_operativo=r.monto*r.porcentaje_operativo/100
            r.monto_ejecutora=r.monto-r.monto_administrativo-r.monto_operativo
    
    @api.depends('monto','porcentaje_administrativo','porcentaje_operativo','line_ids')
    def calcular_disponibles(self):
        for r in self:
            r.disponible_administrativo=r.monto_administrativo
            r.disponible_operativo=r.monto_operativo
            r.disponible_ejecutora=r.monto_ejecutora
            for d in r.line_ids:
                r.disponible_administrativo=r.disponible_administrativo-d.monto_administrativo
                r.disponible_operativo=r.disponible_operativo-d.monto_operativo
                r.disponible_ejecutora=r.disponible_ejecutora-d.monto_ejecutora
        
    
    
class fiaesmoneypack_proyecto(models.Model):
    _name='fiaes.compensacion.pack.proyecto'
    _description= 'Paquete de compensacion y proyecto'
    name=fields.Char("Paquete de compensacion por proyecto",related='pack_id.name')
    monto_administrativo=fields.Float("Monto de gastos administrativo")
    monto_operativo=fields.Float("Monto de gastos operativos")
    monto_ejecutora=fields.Float("Monto de inversion")
    fecha_disponibilidad=fields.Date("Fecha de disponibilidad",related='pack_id.fecha_disponibilidad')
    pack_id=fields.Many2one(comodel_name='fiaes.compensacion.calculo.pack',string="Paquete")
    projecto_ejecutora_id=fields.Many2one(comodel_name='fiaes.ejecutora.proyecto',string="proyecto ejecutora")
    projecto_compensacion_id=fields.Many2one(comodel_name='fiaes.compensacion.proyecto',related='pack_id.projecto_id',string="Proyecto compensacion")
    titular_id=fields.Many2one(comodel_name='res.partner',related='pack_id.titular_id', string='Titular')
    desembolso_ids=fields.One2many(comodel_name='fiaes.compensacion.pack.proyecto.desembolso', inverse_name='pack_proyecto_id')
    total_financiado=fields.Float("Monto financiado",compute='calcular_financiado')
    #Campos relacionados de proyecto de la ejecutora
    componente_id = fields.Many2one(comodel_name='fiaes.inversion',related='projecto_ejecutora_id.componente_id',track_visibility=True,store=True)
    obconservacion = fields.Many2one(string="Objeto de conservacion", related = 'componente_id.conservacion_id',store=True)
    territorio = fields.Many2one(string= "Territorio", related = 'componente_id.territorio_id',store=True) 
    convocatorio = fields.Many2one(string="Convoctoria", related = 'componente_id.convocatoria_id',store=True)
    entidadejutora = fields.Many2one(comodel_name='res.partner',related='projecto_ejecutora_id.entidadejutora',string="Entidad ejecutora",store=True)
    tipoproyecto=fields.Selection(selection=[('Especial', 'Especial')
                                        ,('Convocatoria', 'Convocatoria')]
                                        , string='Tipo de proyecto',related='projecto_ejecutora_id.tipoproyecto',default='Especial',store=True)
    #Campos relacionados al proyecto de compensacion
    resolucion=fields.Char("Numero de resolucion",related='projecto_compensacion_id.resolucion',store=True)
    resolucion_NFA=fields.Char("Numero de resolucion NFA",related='projecto_compensacion_id.resolucion_NFA',store=True)
    resolucion_fecha=fields.Date("Fecha de resolucion",related='projecto_compensacion_id.resolucion_fecha',store=True)
    departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento donde esta la empresa',related='projecto_compensacion_id.departamento_id',store=True)
    municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio donde esta la empresa',related='projecto_compensacion_id.municipio_id',store=True)
    
    @api.one
    @api.depends('desembolso_ids')
    def calcular_financiado(self):
        for r in self:
            total=0.0
            for p in r.desembolso_ids:
                total=total+p.monto_ejecutora
            r.total_financiado=total


class fiaesmoneypack_proyecto_desembolso(models.Model):
    _name='fiaes.compensacion.pack.proyecto.desembolso'
    _description= 'Paquete de compensacion, proyecto y desembolsos'
    name=fields.Char("Paquete de compensacion por proyecto y desembolsos",related='pack_id.name')
    monto_administrativo=fields.Float("Monto de gastos administrativos")
    monto_operativo=fields.Float("Monto de gastos operativos")
    monto_ejecutora=fields.Float("Monto de inversion")
    monto_reintegrado=fields.Float("Monto de reintegrado")
    pack_proyecto_id=fields.Many2one(comodel_name='fiaes.compensacion.pack.proyecto',string="Paquete por proyecto")
    pack_id=fields.Many2one(comodel_name='fiaes.compensacion.calculo.pack',related='pack_proyecto_id.pack_id',string="Paquete")
    anio=fields.Integer("Año a calcular",related="pack_id.anio")
    #Campos relacionados de proyecto de la ejecutora
    projecto_ejecutora_id=fields.Many2one(comodel_name='fiaes.ejecutora.proyecto',related='pack_proyecto_id.projecto_ejecutora_id',string="proyecto ejecutora",store=True)
    componente_id = fields.Many2one(comodel_name='fiaes.inversion',related='projecto_ejecutora_id.componente_id',track_visibility=True,store=True)
    obconservacion = fields.Many2one(string="Objeto de conservacion", related = 'componente_id.conservacion_id',store=True)
    territorio = fields.Many2one(string= "Territorio", related = 'componente_id.territorio_id',store=True) 
    convocatorio = fields.Many2one(string="Convoctoria", related = 'componente_id.convocatoria_id',store=True)
    entidadejutora = fields.Many2one(comodel_name='res.partner',related='projecto_ejecutora_id.entidadejutora',string="Entidad ejecutora",store=True)
    tipoproyecto=fields.Selection(selection=[('Especial', 'Especial')
                                        ,('Convocatoria', 'Convocatoria')]
                                        , string='Tipo de proyecto',related='projecto_ejecutora_id.tipoproyecto',default='Especial',store=True)
    #Campos relacionados al proyecto de compensacion
    projecto_compensacion_id=fields.Many2one(comodel_name='fiaes.compensacion.proyecto',related='pack_proyecto_id.projecto_compensacion_id',string="Proyecto compensacion",store=True)
    titular_id=fields.Many2one(comodel_name='res.partner',related='pack_proyecto_id.titular_id', string='Titular',store=True)
    resolucion=fields.Char("Numero de resolucion",related='projecto_compensacion_id.resolucion',store=True)
    resolucion_NFA=fields.Char("Numero de resolucion NFA",related='projecto_compensacion_id.resolucion_NFA',store=True)
    resolucion_fecha=fields.Date("Fecha de resolucion",related='projecto_compensacion_id.resolucion_fecha',store=True)
    departamento_id=fields.Many2one(comodel_name='fiaes.departamento', string='Departamento donde esta la empresa',related='projecto_compensacion_id.departamento_id',store=True)
    municipio_id=fields.Many2one(comodel_name='fiaes.municipio', string='Municipio donde esta la empresa',related='projecto_compensacion_id.municipio_id',store=True)
    #Desembolso
    desembolso_id=fields.Many2one(comodel_name='fiaes.ejecutora.desembolso', string='Desembolso')
    state_desembolso=fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Aplicado', 'Aplicado')
                                        ,('Reintegro', 'Reintegro iniciado')
                                        ,('Reintegrado', 'Reintegrado')]
                                        , string='Estado',default='Borrador',related='desembolso_id.state')
    fecha_desembolso=fields.Date("Fecha",related='desembolso_id.fechafiaes',store=True)
    operativo_transferencia_id=fields.Many2one(comodel_name='fiaes.compensacion.transferencia', string='Transferencia gastos operativo')
    administrativo_transferencia_id=fields.Many2one(comodel_name='fiaes.compensacion.transferencia', string='Transferencia gastos administrativo')

    @api.constrains('monto_ejecutora','monto_reintegrado')
    def check_montos(self):
        for r in self:
            if r.monto_reintegrado>r.monto_ejecutora:
                raise ValidationError("No  reintegrar mas dinero del otorgado")
    
    
    
class fiaesmoneypack_gastos(models.Model):
    _name='fiaes.compensacion.transferencia'
    _description= 'Transferencias de gastos'
    _inherit= ['mail.thread']
    tipo_gasto=fields.Selection(selection=[('Administrativo', 'Administrativo')
                                        ,('Operativo', 'Operativo')]
                                        , string='Tipo de transferencia',default='Administrativo')
    name=fields.Char("Paquete de transferencia de gastos")
    monto=fields.Float("Monto de gastos administrativo/operativos")
    monto_financiado=fields.Float("Monto de gastos financiado administrativo/operativos",compute='calcular_financiado')
    anio=fields.Integer("Año a calcular")
    fecha=fields.Date("Fecha de validacion")
    administrativo_desembolso_ids=fields.One2many(comodel_name='fiaes.compensacion.pack.proyecto.desembolso', inverse_name='administrativo_transferencia_id')
    operativo_desembolso_ids=fields.One2many(comodel_name='fiaes.compensacion.pack.proyecto.desembolso', inverse_name='operativo_transferencia_id')
    move_id= fields.Many2one(comodel_name='account.move',string="Movimiento contable")
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Aplicado', 'Aplicado')]
                                        , string='Estado',default='Borrador')
    
    @api.one
    def calcular(self):
        for r in self:
            type='administrativo_desembolso_ids'
            child_field='administrativo_transferencia_id'
            child_amount_field='monto_administrativo'
            total_a_comparar=r.monto
            if (r.tipo_gasto=='Operativo'):
                type='operativo_desembolso_ids'
                child_field='operativo_transferencia_id'
                child_amount_field='monto_operativo'
            if r.administrativo_desembolso_ids:
                for d in r.administrativo_desembolso_ids:
                    d.administrativo_transferencia_id=None
            if r.operativo_desembolso_ids:
                for d in r.operativo_desembolso_ids:
                    d.operativo_transferencia_id=None
            #Calculando los que han sido desembolsados
            desembolsos=self.env['fiaes.compensacion.pack.proyecto.desembolso'].search([('anio','=',r.anio),(child_field,'=',False),('state_desembolso','!=','Borrador')],order=child_amount_field)
            total=0.0
            for d in desembolsos:
                if total<total_a_comparar:
                    if (r.tipo_gasto=='Operativo'):
                        if d.monto_operativo>0:
                            total=total+d.monto_operativo
                            d.operativo_transferencia_id=r.id
                    else:
                        if d.monto_administrativo>0:
                            total=total+d.monto_administrativo
                            d.administrativo_transferencia_id=r.id
    
    @api.one
    @api.depends('administrativo_desembolso_ids','operativo_desembolso_ids')
    def calcular_financiado(self):
        for r in self:
            if (r.tipo_gasto=='Operativo'):
                monto_financiado=0.0
                for p in r.operativo_desembolso_ids:
                    monto_financiado=monto_financiado+p.monto_operativo
                r.monto_financiado=monto_financiado
            else:
                monto_financiado=0.0
                for p in r.administrativo_desembolso_ids:
                    monto_financiado=monto_financiado+p.monto_administrativo
                r.monto_financiado=monto_financiado
    
    @api.multi
    def aplicar(self):
        company=self.env['res.company'].search([('id','=',1)],limit=1)
        for r in self:
            dic={}
            dic['journal_id']=company.compensacion_journal_id.id
            dic['date']=datetime.strftime(datetime.now(), '%Y-%m-%d')
            r.fecha=datetime.strftime(datetime.now(), '%Y-%m-%d')
            lines=[]
            if (r.tipo_gasto=='Operativo'):
                dic['sv_concepto']='Traslado de Gastos Operativos'
                for d in r.operativo_desembolso_ids:
                    cargo_operativo_account=company.operativo_especial_cargo_account_id.id
                    abono_operativo_account=company.operativo_especial_abono_account_id.id
                    if d.projecto_ejecutora_id.tipoproyecto=='Convocatoria':
                        cargo_operativo_account=company.operativo_especifico_cargo_account_id.id
                        abono_operativo_account=company.operativo_especifico_abono_account_id.id
                    if d.monto_operativo>0:
                        cargo1={}
                        cargo1['name']='Traslado de gastos operativos:'+d.titular_id.name+' '+d.projecto_compensacion_id.name
                        cargo1['partner_id']=d.titular_id.id
                        cargo1['account_id']=cargo_operativo_account
                        cargo1['credit']=d.monto_operativo
                        cargo1['debit']=0
                        cargo=(0,0,cargo1)
                        abono1={}
                        abono1['name']='Traslado de gastos operativos:'+d.titular_id.name+' '+d.projecto_compensacion_id.name
                        abono1['partner_id']=d.titular_id.id
                        abono1['account_id']=abono_operativo_account
                        abono1['credit']=0
                        abono1['debit']=d.monto_operativo
                        abono=(0,0,abono1)
                        lines.append(cargo)
                        lines.append(abono)
            else:
                dic['sv_concepto']='Traslado de Gastos Administrativos'
                for d in r.administrativo_desembolso_ids:
                    cargo_administratrivo_account=company.administrativo_especial_cargo_account_id.id
                    abono_administrativo_account=company.administrativo_especial_abono_account_id.id
                    if d.projecto_ejecutora_id.tipoproyecto=='Convocatoria':
                        cargo_administratrivo_account=company.administrativo_especifico_cargo_account_id.id
                        abono_administrativo_account=company.administrativo_especifico_abono_account_id.id
                    if d.monto_administrativo>0:
                        cargo1={}
                        cargo1['name']='Traslado de gastos administrativos:'+d.titular_id.name+' '+d.projecto_compensacion_id.name
                        cargo1['partner_id']=d.titular_id.id
                        cargo1['account_id']=cargo_administratrivo_account
                        cargo1['credit']=d.monto_administrativo
                        cargo1['debit']=0
                        cargo=(0,0,cargo1)
                        abono1={}
                        abono1['name']='Traslado de gastos administrativos:'+d.titular_id.name+' '+d.projecto_compensacion_id.name
                        abono1['partner_id']=d.titular_id.id
                        abono1['account_id']=abono_administrativo_account
                        abono1['credit']=0
                        abono1['debit']=d.monto_administrativo
                        abono=(0,0,abono1)
                        lines.append(cargo)
                        lines.append(abono)
            dic['line_ids']=lines
            move=self.env['account.move'].create(dic)
            r.move_id=move.id
            r.state='Aplicado'