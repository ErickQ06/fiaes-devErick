
import uuid
#from . import numero_letras
from odoo import api, models, fields, _
from datetime import datetime, timedelta,date
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.safe_eval import safe_eval
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__) 



class prespuesto(models.Model):
    _name='fiaes.presupuesto'
    _inherit= ['mail.thread']
    _description='Presupuesto anual'
    name= fields.Char("Presupuesto",track_visibility=True)
    anio= fields.Char("Anio",track_visibility=True)
    state= fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado', required=True, default='Borrador',track_visibility=True)
    comentario=fields.Text("Comentario")
    line_ids=fields.One2many('fiaes.presupuesto.line','presupuesto_id',string='Desembolsos')
    planilla_plan=fields.Many2one('fiaes.planunidad',string='Plan que contiene las planillas')
    
    @api.one
    def calcular(self):
        for r in self:
            #borrando los presupuestos anteriores
            self.env['fiaes.presupuesto.line'].search([('presupuesto_id','=',r.id)]).unlink()
            insumos=self.env['fiaes.insumo'].search([('anio','=',r.anio)])
            for insumo in insumos:
                line=self.env['fiaes.presupuesto.line'].search([('presupuesto_id','=',r.id),('planunidad_id','=',insumo.planunidad_id.id),('proyecto_id','=',insumo.proyecto.id),('actividad_id','=',insumo.actividad_id.id),('account_id','=',insumo.cuenta_id.id),('mes','=',insumo.mes),('fuente_id','=',insumo.fuente.id)])
                if line:
                    line.monto_presupuestado=line.monto_presupuestado+insumo.total
                else:
                    dic={}
                    dic['presupuesto_id']=r.id
                    dic['planunidad_id']=insumo.planunidad_id.id
                    dic['proyecto_id']=insumo.proyecto.id
                    dic['actividad_id']=insumo.actividad_id.id
                    dic['account_id']=insumo.cuenta_id.id
                    dic['mes']=insumo.mes
                    dic['fuente_id']=insumo.fuente.id
                    dic['monto_presupuestado']=insumo.total
                    self.env['fiaes.presupuesto.line'].create(dic)
                    
    @api.one
    def calcular_planilla(self):
        for r in self:
            #creando el plan
            poa=self.env['fiaes.poa'].search([('anio','=',r.anio)],limit=1)
            company=self.env['res.company'].browse(1)
            plan=self.env['fiaes.planunidad'].search([('poa_id','=',poa.id),('unidad','=',company.planilla_unidad_id.id)],limit=1)
            if plan:
                self.env['fiaes.insumo'].search([('planunidad_id','=',plan.id)]).unlink()
                self.env['fiaes.poaobjetivos'].search([('planunidad_id','=',plan.id)]).unlink()
                self.env['fiaes.poaactividad'].search([('planunidad_id','=',plan.id)]).unlink()
            else:
                dic={}
                dic['unidad']=company.planilla_unidad_id.id
                dic['poa_id']=poa.id
                dic['state']='Aprobado'
                plan=self.env['fiaes.planunidad'].create(dic)
            #creando el objetivo operativo
            dic={}
            dic['name']='Planillas'
            dic['planunidad_id']=plan.id
            dic['vinculado_pei']=False
            dic['descripcion']='Planillas'
            objetivo=self.env['fiaes.poaobjetivos'].create(dic)
            #recorriendo los contratos
            r.planilla_plan=plan.id
            contratos=self.env['hr.contract'].search([('date_start','>=',str(r.anio)+'-01-01'),('date_start','<=',str(r.anio)+'-12-31')])
            _logger.info('Calculo contratos:')
            for c in contratos:
                _logger.info('Dentro de contrato')
                tablas={}
                cuentas={}
                if not c.perfil_id:
                    raise ValidationError('El contrato %s no tiene perfil asociado' % c.name)
                for t in c.perfil_id.line_ids:
                    tablas[str(t.tipo_id.id)]=t.prorrateo_id
                    cuentas[str(t.tipo_id.id)]=t.cuenta_id
                variables={}
                variables['sueldo']=c.wage
                variables['sueldo_diario']=c.sueldo_dia
                for var in c.line_valor:
                    variables[var.name]=var.valor
                for formula in company.tipo_line:
                    _logger.info('Calculo formula:'+formula.formula)
                    valor=float(safe_eval(formula.formula, variables))
                    tabla=tablas[str(formula.id)]
                    cuenta=cuentas[str(formula.id)]
                    calculo=formula.name
                    if (formula.tipo=='Mensual'):
                        r.crear_detalles(c,valor,'01',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'02',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'03',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'04',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'05',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'06',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'07',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'08',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'09',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'10',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'11',objetivo,tabla,cuenta,calculo)
                        r.crear_detalles(c,valor,'12',objetivo,tabla,cuenta,calculo)
                    else:
                        r.crear_detalles(c,valor,formula.mes,objetivo,tabla,cuenta,calculo)
                        
    @api.one
    def crear_detalles(self,contract,valor,mes,obj,tabla,cuenta,calculo):
        #prorateando por contrato
        for r in self:
            for f in tabla.line_ids:
                new_valor=(valor*f.porcentaje)/100
                actividad=self.env['fiaes.poaactividad'].search([('proyecto','=',f.proyecto_id.id),('objetivopoa_id','=',obj.id)],limit=1)
                if not actividad:
                    dic={}
                    dic['name']='Salarios:'+f.proyecto_id.name 
                    dic['descripcion']='Salarios:'+f.proyecto_id.name 
                    dic['proyecto']=f.proyecto_id.id
                    dic['objetivopoa_id']=obj.id
                    dic['fecha_inicial']=str(r.anio)+'-01-01'
                    dic['fecha_final']=str(r.anio)+'-12-31'
                    dic['planunidad_id']=obj.planunidad_id.id
                    dic['state']='Aprobado'
                    actividad=self.env['fiaes.poaactividad'].create(dic)
                newdic={}
                newdic['name']=' Salario '+ mes+ ' contrato:'+contract.name+' - '+calculo
                newdic['actividad_id']=actividad.id
                newdic['preciouni']=new_valor
                newdic['cantidad']=1
                newdic['mes']=mes
                newdic['fuente']=f.fuente_id.id
                newdic['cuenta_id']=cuenta.id
                self.env['fiaes.insumo'].create(newdic)

            
    
    @api.one
    def aprobar(self):
        for r in self:
            r.state='Aprobado'
    
    @api.one
    def cancelar(self):
        for r in self:
            r.state='Cancelado'
    
    
class presupuesto_line(models.Model):
    _name='fiaes.presupuesto.line'
    _inherit= ['mail.thread']
    _description='Detalle Presupuesto anual'
    name= fields.Char("Presupuesto detalle",compute='compute_name',track_visibility=True)
    presupuesto_id=fields.Many2one(comodel_name='fiaes.presupuesto', string='Presupuesto')
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad', string="Plan unidad")
    proyecto_id=fields.Many2one(comodel_name='project.project', string='Proyecto')
    fuente_id=fields.Many2one(comodel_name='fiaes.fuente', string='Fuente de financamiento')
    actividad_id=fields.Many2one(comodel_name='fiaes.poaactividad', string='actividad')
    account_id=fields.Many2one(comodel_name='account.account', string='Cuenta')
    mes = fields.Selection([('01','Enero'),('02','Febrero'),('03','Marzo'),('04','Abril'),('05','Mayo'),('06','Junio'),('07','Julio'),('08','Agosto'),('09','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')])
    monto_presupuestado=fields.Float("Monto presupuestado")
    monto_ejecutado=fields.Float("Monto ejecutador")
    
    
    
    
    @api.one
    def compute_name(self):
        for r in self:
            r.name='Detalle de presupuesto'
            
            

class purchase_insumo(models.Model):
    _inherit='purchase.order.line'
    actividad_id=fields.Many2one(comodel_name='fiaes.poaactividad', string='Actividad')
    insumo_id=fields.Many2one(comodel_name='fiaes.insumo', string='Bien/Servicio')
    fuente_id=fields.Many2one(comodel_name='fiaes.fuente',related='insumo_id.fuente', string='Fuente')
    proyecto_id=fields.Many2one(comodel_name='project.project',related='actividad_id.proyecto', string='Proyecto',store=True)
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad',related='actividad_id.planunidad_id', string="Plan unidad",store=True)
    poa_id = fields.Many2one(comodel_name='fiaes.poa', string="POA",related='planunidad_id.poa_id',store=True)
    state=fields.Selection(selection=[('draft', 'Borrador')
                                    ,('sent', 'Enviado')
                                    ,('pruchase', 'Confirmado')
                                    ,('sent', 'Enviado')
                                    ,('done', 'done')
                                    ,('cancel', 'cancel')
                                    ,('to approve', 'A aprobacion')]
                                    , string='Estado',related="order_id.state")


class purchase_insumo_order(models.Model):
    _inherit='purchase.order'
    @api.multi
    def button_confirm(self):
        #do task before confirm
        for r in self:
            for l in r.order_line:
                if l.insumo_id:
                    insumo=self.env['fiaes.insumo'].browse(l.insumo_id.id)
                    insumo.ejecutado=True
        res=super(purchase_insumo_order,self).button_confirm()        
        #do task after confirm by using res
        return res
