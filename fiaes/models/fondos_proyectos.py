# -*- coding: utf-8 -*-
##############################################################################

import math 
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class fondosproyectofiaes(models.Model):
    _name='fiaes.ejecutora.proyecto'
    _inherit= ['mail.thread']
    name = fields.Char(string="Name")
    anio=fields.Integer("Año")
    id_proyecto = fields.Integer(track_visibility=True)
    coordenadas_latitud=fields.Float("Latitud",digits=(20,7))
    coordenadas_longitud=fields.Float("Longitud",digits=(20,7))
    componente_id = fields.Many2one(comodel_name='fiaes.inversion',track_visibility=True)
    obconservacion = fields.Many2one(string="Objeto de conservacion", related = 'componente_id.conservacion_id')
    territorio = fields.Many2one(string= "Territorio", related = 'componente_id.territorio_id') 
    convocatorio = fields.Many2one(string="Convoctoria", related = 'componente_id.convocatoria_id')
    entidadejutora = fields.Many2one(comodel_name='res.partner',string="Entidad ejecutora")
    tipoproyecto=fields.Selection(selection=[('Especial', 'Especial')
                                        ,('Convocatoria', 'Convocatoria')]
                                        , string='Tipo de Activo',default='Especial')
    line_fiaesdes = fields.One2many(comodel_name='fiaes.ejecutora.desembolso', inverse_name='proyect_id')
    line_cotrasdes = fields.One2many(comodel_name='fiaes.ejecutora.desembolsoscontrapartida', inverse_name='proyect_id')
    line_producto = fields.One2many(comodel_name='fiaes.ejecutora.producto', inverse_name='proyect_id')
    line_indicadores = fields.One2many(comodel_name='fiaes.ejecutora.indicadores', inverse_name='proyect_id')
    line_actividad = fields.One2many(comodel_name='fiaes.ejecutora.actividad', inverse_name='proyect_id')
    pack_disponible_ids=fields.One2many(comodel_name='fiaes.ejecutora.proyecto.disponible.pack', inverse_name='projecto_ejecutora_id')
    pack_includes_ids=fields.One2many(comodel_name='fiaes.compensacion.pack.proyecto', inverse_name='projecto_ejecutora_id')
    total_financiar=fields.Float("Monto a financiar",compute="calcular_financiamiento")
    total_financiado=fields.Float("Monto financiado",compute="calcular_financiamiento")
    pack_desembolso_ids=fields.One2many(comodel_name='fiaes.compensacion.pack.proyecto.desembolso', inverse_name='projecto_ejecutora_id')
    
    
    @api.one
    @api.depends('line_fiaesdes','pack_includes_ids')
    def calcular_financiamiento(self):
        for r in self:
            financiar=0
            financiado=0
            for d in r.line_fiaesdes:
                if d.fechafiaes:
                    if d.fechafiaes.year==r.anio:
                        financiar=financiar+d.valorfiaes
            for p in r.pack_includes_ids:
                financiado=financiado+p.monto_ejecutora
            r.total_financiar=financiar
            r.total_financiado=financiado
            # cuales proyectos tienen esta afectacion
            #agregar boton para gastos admin y op
    
    @api.multi
    def calcular_disponible(self):
        for r in self:
            calculo=self.env['fiaes.compensacion.calculo'].search([('anio','=',r.anio)],limit=1)
            proyectos={}# distancias de los proyectos que aplican
            if calculo:
                for p in calculo.desembolso_ids:
                    for afectacion in p.projecto_id.afectacion_ids:
                        for conservacion in afectacion.conservacion_ids:
                            if conservacion.id==r.obconservacion.id:
                                if r.coordenadas_latitud and r.coordenadas_longitud and p.projecto_id.coordenadas_latitud and p.projecto_id.coordenadas_longitud:
                                    origin=(r.coordenadas_latitud,r.coordenadas_longitud)
                                    destination=(p.projecto_id.coordenadas_latitud,p.projecto_id.coordenadas_longitud)
                                    proyectos[str(p.projecto_id.id)]=r.distance(origin,destination)
                                else:
                                    proyectos[str(p.projecto_id.id)]=0.0
            for key in proyectos:
                #raise ValidationError('Condicion:%s  '% proyectos[key] )
                packs=self.env['fiaes.compensacion.calculo.pack'].search([('projecto_id','=',int(key)),('calculo_id','=',calculo.id)])
                for pack in packs:
                    if pack.disponible_ejecutora>0:
                        dic={}
                        dic['pack_id']=pack.id
                        dic['distancia']=proyectos[key]
                        dic['projecto_ejecutora_id']=r.id
                        self.env['fiaes.ejecutora.proyecto.disponible.pack'].create(dic)
    @api.one
    def calcular_desembolsos(self):
        for r in self:
            for desembolso in r.line_fiaesdes:
                if desembolso.fechafiaes.year==r.anio:
                    if desembolso.total_financiado<desembolso.valorfiaes:
                        dif=desembolso.valorfiaes-desembolso.total_financiado
                        paquetes=r.pack_includes_ids.sorted(key=lambda r: (r.fecha_disponibilidad, r.monto_ejecutora))
                        for pack in paquetes:
                            disponiblepack=pack.monto_ejecutora-pack.total_financiado
                            if disponiblepack>0:
                                if dif>disponiblepack:
                                    monto=disponiblepack
                                else:
                                    monto=dif
                                if monto>0:
                                    dic={}
                                    dic['monto_ejecutora']=monto
                                    dic['monto_administrativo']=monto*pack.pack_id.porcentaje_administrativo/100
                                    dic['monto_operativo']=monto*pack.pack_id.porcentaje_operativo/100
                                    dic['pack_proyecto_id']=pack.id
                                    dic['desembolso_id']=desembolso.id
                                    self.env['fiaes.compensacion.pack.proyecto.desembolso'].create(dic)
                                dif=dif-monto
        
    
    def distance(self, origin, destination): 
        lat1, lon1 = origin 
        lat2, lon2 = destination 
        radius = 6371 # km 

        dlat = math.radians(lat2 - lat1) 
        dlon = math.radians(lon2 - lon1) 
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
        math.sin(dlon/2) * math.sin(dlon/2)) 
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)) 
        d = radius * c 
        return d 
    


#detalle       
#Desembolsos FIAES                              
class fondosdesmbolsosfiaes(models.Model):
    _name = 'fiaes.ejecutora.desembolso'   
    _inherit= ['mail.thread']
    valorfiaes = fields.Float(string="Valor")
    fechafiaes = fields.Date(string="Fecha prevista")
    proyect_id = fields.Many2one(comodel_name='fiaes.ejecutora.proyecto',string='Proyecto ejecutora')
    pack_includes_ids=fields.One2many(comodel_name='fiaes.compensacion.pack.proyecto.desembolso', inverse_name='desembolso_id')
    total_financiado=fields.Float("Monto financiado",compute='calcular_financiado')
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                        ,('Aplicado', 'Aplicado')
                                        ,('Reintegro', 'Reintegro iniciado')
                                        ,('Reintegrado', 'Reintegrado')]
                                        , string='Estado',default='Borrador')
    fecha_aplicacion=fields.Date("Fecha de aplicacion")
    componente_id = fields.Many2one(comodel_name='fiaes.inversion',track_visibility=True,related='proyect_id.componente_id')
    obconservacion = fields.Many2one(string="Objeto de conservacion", related = 'componente_id.conservacion_id')
    territorio = fields.Many2one(string= "Territorio", related = 'componente_id.territorio_id') 
    convocatorio = fields.Many2one(string="Convoctoria", related = 'componente_id.convocatoria_id')
    entidadejutora = fields.Many2one(comodel_name='res.partner',string="Entidad ejecutora",related='proyect_id.entidadejutora')
    move_id= fields.Many2one(comodel_name='account.move',string="Movimiento contable")
    reintegro_move_id= fields.Many2one(comodel_name='account.move',string="Movimiento contable de reintegro")
    tipoproyecto=fields.Selection(selection=[('Especial', 'Especial')
                                        ,('Convocatoria', 'Convocatoria')]
                                        , string='Tipo de Activo',default='Especial',related='proyect_id.tipoproyecto')
    total_reintegrado=fields.Float("Monto reintegrado",compute='calcular_financiado')
    
    
    @api.one
    @api.depends('pack_includes_ids')
    def calcular_financiado(self):
        for r in self:
            total=0.0
            totalr=0.0
            for p in r.pack_includes_ids:
                total=total+p.monto_ejecutora
                totalr=totalr+p.monto_reintegrado
            r.total_financiado=total
            r.total_reintegrado=totalr
    
    @api.one
    def iniciar_reintegro(self):
        for r in self:
            r.state='Reintegro'
            
    @api.multi
    def aplicar(self):
        company=self.env['res.company'].search([('id','=',1)],limit=1)
        for r in self:
            cargo_account=company.inversion_especial_cargo_account_id.id
            abono_account=company.inversion_especial_abono_account_id.id
            if r.proyect_id.tipoproyecto=='Convocatoria':
                cargo_account=company.inversion_especifico_cargo_account_id.id
                abono_account=company.inversion_especifico_abono_account_id.id
            dic={}
            dic['journal_id']=company.compensacion_journal_id.id
            dic['date']=datetime.strftime(datetime.now(), '%Y-%m-%d')
            dic['sv_concepto']='Desembolos a ejecutaroa:'+r.proyect_id.entidadejutora.name+' '+r.proyect_id.name
            dic['partner_id']=r.proyect_id.entidadejutora.id
            lines=[]
            for d in r.pack_includes_ids:
                cargo={}
                cargo['name']='Desembolos a ejecutaroa:'+r.proyect_id.entidadejutora.name+' '+r.proyect_id.name
                cargo['partner_id']=r.proyect_id.entidadejutora.id
                cargo['account_id']=cargo_account
                cargo['credit']=d.monto_ejecutora
                cargo['debit']=0
                abono={}
                abono['name']='Desembolos a ejecutaroa:'+r.proyect_id.entidadejutora.name+' '+r.proyect_id.name
                abono['partner_id']=r.proyect_id.entidadejutora.id
                abono['account_id']=abono_account
                abono['credit']=0
                abono['debit']=d.monto_ejecutora
                abono1=(0,0,abono)
                cargo1=(0,0,cargo)
                lines.append(cargo1)
                lines.append(abono1)
            dic['line_ids']=lines
            move=self.env['account.move'].create(dic)
            r.move_id=move.id
            r.state='Aplicado'
            
    @api.multi ### todo hay que hacer movimeinto por titular
    def revertir(self):
        company=self.env['res.company'].search([('id','=',1)],limit=1)
        for r in self:
            cargo_account=company.inversion_especial_abono_account_id.id
            abono_account=company.inversion_especial_cargo_account_id.id
            if r.proyect_id.tipoproyecto=='Convocatoria':
                cargo_account=company.inversion_especifico_abono_account_id.id
                abono_account=company.inversion_especifico_cargo_account_id.id
            dic={}
            dic['journal_id']=company.compensacion_journal_id.id
            dic['date']=datetime.strftime(datetime.now(), '%Y-%m-%d')
            dic['sv_concepto']='Reintegro de desembolos a ejecutaroa:'+r.proyect_id.entidadejutora.name+' '+r.proyect_id.name
            dic['partner_id']=r.proyect_id.entidadejutora.id
            lines=[]
            for d in r.pack_includes_ids:
                if d.monto_reintegrado>0:
                    cargo={}
                    cargo['name']='Reintegro de desembolos a ejecutaroa:'+r.proyect_id.entidadejutora.name+' '+r.proyect_id.name
                    cargo['partner_id']=r.proyect_id.entidadejutora.id
                    cargo['account_id']=cargo_account
                    cargo['credit']=d.monto_reintegrado
                    cargo['debit']=0
                    abono={}
                    abono['name']='Reintegro de desembolos a ejecutaroa:'+r.proyect_id.entidadejutora.name+' '+r.proyect_id.name
                    abono['partner_id']=r.proyect_id.entidadejutora.id
                    abono['account_id']=abono_account
                    abono['credit']=0
                    abono['debit']=d.monto_reintegrado
                    abono1=(0,0,abono)
                    cargo1=(0,0,cargo)
                    lines.append(cargo1)
                    lines.append(abono1)
                    proyecto=self.env['fiaes.compensacion.proyecto'].search([('id','=',d.projecto_compensacion_id.id)],limit=1)
                    if proyecto:
                        proyecto.disponible_con_gastos=proyecto.disponible_con_gastos+d.monto_reintegrado
            dic['line_ids']=lines
            move=self.env['account.move'].create(dic)
            r.move_id=move.id
            r.state='Reintegrado'
                
        
  


    #Desembolso contrapartadita
class fondosdesmbolsoscontra(models.Model):
    _name = 'fiaes.ejecutora.desembolsoscontrapartida'  
    monto = fields.Float(string="Monto")
    numero = fields.Float(string="Numero desembolso")
    fechacontrpartida = fields.Date(string="Fecha prevista")
    proyect_id = fields.Many2one(comodel_name='fiaes.ejecutora.proyecto')

   #Producto 
class fondosproyectoproducto(models.Model):   
    _name='fiaes.ejecutora.producto'
    nombreproducto = fields.Char(string="Nombre")
    codigoproducto = fields.Char(string="Codigo")
    proyect_id = fields.Many2one(comodel_name='fiaes.ejecutora.proyecto')

    #Actividad
class fondosproyectoactividad(models.Model):
    _name = 'fiaes.ejecutora.actividad'
    nombreactividad = fields.Char(string="Nombre")
    codigoactividad = fields.Char(string="Codigo")
    proyect_id = fields.Many2one(comodel_name='fiaes.ejecutora.proyecto')

    #Indicadores y metas
class fondosproyectosindicadores(models.Model):
    _name='fiaes.ejecutora.indicadores'
    indicador_id = fields.Many2one(comodel_name='fiaes.indicador', string="Indicador")
    meta = fields.Char(string="Meta")
    proyect_id = fields.Many2one(comodel_name='fiaes.ejecutora.proyecto')
    


class fondo_disponible(models.Model):
    _name='fiaes.ejecutora.proyecto.disponible.pack'
    _description='Pack de compensacion disponible'
    name=fields.Char("Paquete de compensacion",related="pack_id.name")
    pack_id=fields.Many2one(comodel_name='fiaes.compensacion.calculo.pack',string='Paquete de compensacion')
    distancia=fields.Float("Distancia")
    projecto_ejecutora_id=fields.Many2one(comodel_name='fiaes.ejecutora.proyecto',string='Proyecto ')
    monto_ejecutora=fields.Float("Monto de inversion",related="pack_id.monto_ejecutora",store=True)
    fecha_disponibilidad=fields.Date("Fecha de disponibilidad",related="pack_id.fecha_disponibilidad",store=True)
    disponible_administrativo=fields.Float("Monto disponible de gastos administrativo",related="pack_id.disponible_administrativo",store=True)
    disponible_operativo=fields.Float("Monto disponible de gastos operativos",related="pack_id.disponible_operativo",store=True)
    disponible_ejecutora=fields.Float("Monto disponible de inversion",related="pack_id.disponible_ejecutora",store=True)
    
    @api.one
    def addionar_pack(self):
        for r in self:
            dif=r.projecto_ejecutora_id.total_financiar-r.projecto_ejecutora_id.total_financiado
            if dif>0:
                monto=r.monto_ejecutora
                if dif<r.monto_ejecutora:
                    monto=dif
                dic={}
                dic['monto_ejecutora']=monto
                dic['monto_administrativo']=monto*r.pack_id.porcentaje_administrativo/100
                dic['monto_operativo']=monto*r.pack_id.porcentaje_operativo/100
                dic['pack_id']=r.pack_id.id
                dic['projecto_ejecutora_id']=r.projecto_ejecutora_id.id
                self.env['fiaes.compensacion.pack.proyecto'].create(dic)
            


