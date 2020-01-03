from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.safe_eval import safe_eval
from odoo import SUPERUSER_ID


class reportPlan(models.Model):
    _name = 'fiaes.reporte.plan'
    _description='Reporte de un plan de unidad'
    _inherit= ['mail.thread']
    name = fields.Char(string="Reporte",compute='_compute_name')
    plan_id = fields.Many2one(comodel_name='fiaes.planunidad',required=True)
    fecha = fields.Date(string="Fecha",required=True)
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado',required=True,default='Borrador',track_visibility=True)
    variable_ids=fields.One2many('fiaes.reporte.variable','report_id',string='Variables')
    resultado_ids=fields.One2many('fiaes.reporte.resultado','report_id',string='Resultados')
    indicador_ids=fields.One2many('fiaes.reporte.indicador','report_id',string='Indicadores')
    
    @api.one
    def aprobar(self):
        for r in self:
            r.state='Aprobado'
    
    @api.one
    def regresar(self):
        for r in self:
            r.state='Borrador'
    
    @api.one
    def cancelar(self):
        for r in self:
            r.state='Cancelado'

    
    @api.one
    @api.depends('plan_id','fecha')
    def _compute_name(self):
        for r in self:
            if r.plan_id:
                if r.fecha:
                    r.name=r.plan_id.name+' '+r.fecha.strftime("%m/%d/%Y")
    
    @api.one
    def generate_items(self):
        for r in self:
            if r.plan_id:
                for o in r.plan_id.objetivo_line:
                    for i in o.indicador_line:
                        #TODO:crear el indicador
                        dic={}
                        dic["poaindicador_id"]=i.id
                        dic["indicador_id"]=i.indicador_id.id
                        dic["objetivopoa_id"]=o.id
                        dic["valor"]=0.0
                        dic["report_id"]=r.id
                        previo=0.0
                        previos=self.env['fiaes.reporte.indicador'].search(['&',('poaindicador_id','=',i.id),('plan_id','=',r.plan_id.id),('report_id','!=',r.id),('fecha','<',r.fecha)])
                        for p in previos:
                            previo=previo+p.valor
                        dic["valor_previo"]=previo
                        existe=self.env['fiaes.reporte.indicador'].search(['&',('poaindicador_id','=',i.id),('report_id','=',r.id)],limit=1)
                        if not existe:
                            self.env['fiaes.reporte.indicador'].create(dic)
                        
                        for v in i.indicador_id.variable_ids:
                            dic={}
                            dic["variable_id"]=v.id
                            dic["objetivopoa_id"]=o.id
                            dic["valor"]=0.0
                            dic["report_id"]=r.id
                            previo=0.0
                            previos=self.env['fiaes.reporte.variable'].search(['&',('variable_id','=',v.id),('plan_id','=',r.plan_id.id),('report_id','!=',r.id),('fecha','<',r.fecha)])
                            for p in previos:
                                previo=previo+p.valor
                            dic["valor_previo"]=previo
                            existe=self.env['fiaes.reporte.variable'].search(['&',('variable_id','=',v.id),('report_id','=',r.id)],limit=1)
                            if not existe:
                                self.env['fiaes.reporte.variable'].create(dic)
                    for a in o.actividad_line:
                        for re in a.resultados_line:
                            dic={}
                            dic["resultado_id"]=re.id
                            dic["objetivopoa_id"]=o.id
                            dic["valor"]=0.0
                            dic["report_id"]=r.id
                            previo=0.0
                            previos=self.env['fiaes.reporte.resultado'].search(['&',('resultado_id','=',re.id),('plan_id','=',r.plan_id.id),('report_id','!=',r.id),('fecha','<',r.fecha)])
                            for p in previos:
                                previo=previo+p.valor
                            dic["valor_previo"]=previo
                            existe=self.env['fiaes.reporte.resultado'].search(['&',('resultado_id','=',v.id),('report_id','=',r.id)],limit=1)
                            if not existe:
                                self.env['fiaes.reporte.resultado'].create(dic)
    @api.one
    def calcular_indicador(self):
        for r in self:
            for i in r.indicador_ids:
                dic={}
                for v in r.variable_ids:
                    if v.indicador_id.id==i.indicador_id.id:
                        dic[v.codigo]=v.valor
                i.valor=float(safe_eval(i.forma_calculo, dic))


class report_varriable(models.Model):
    _name='fiaes.reporte.variable'
    _description='variable del indicador'
    name = fields.Char(string="variable",related='variable_id.name')
    codigo = fields.Char(string="variable",related='variable_id.codigo')
    variable_id=fields.Many2one(comodel_name='fiaes.indicador.variable',required=True,string='Variable')
    indicador_id=fields.Many2one(comodel_name='fiaes.indicador',related="variable_id.indicador_id",required=True,string='Indicador')
    objetivopoa_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',string="Objetivo Operativo",track_visibility=True)
    comentario=fields.Char("Comentario")
    valor=fields.Float("Avance del periodo")
    valor_previo=fields.Float("Avance acumulado anterior")
    valor_acumulado=fields.Float("Avance acumulado",compute='_compute_acumulado')
    report_id=fields.Many2one(comodel_name='fiaes.reporte.plan',string="Reporte",track_visibility=True)
    plan_id = fields.Many2one(comodel_name='fiaes.planunidad',related='report_id.plan_id',required=True)
    fecha = fields.Date(string="Fecha",related='report_id.fecha')
    document = fields.Binary(string="documento",track_visibility=True)
    file_name=fields.Char("file name")
    
    @api.one
    @api.depends('valor','valor_previo')
    def _compute_acumulado(self):
        for r in self:
            r.valor_acumulado=r.valor+r.valor_previo


class report_resultado(models.Model):
    _name='fiaes.reporte.resultado'
    _description='Resultados'
    name = fields.Char(string="Resultado",related='resultado_id.name')
    resultado_id=fields.Many2one(comodel_name='fiaes.resultado',required=True,string='Variable')
    actividad_id=fields.Many2one(comodel_name='fiaes.poaactividad',related='resultado_id.actividad_id',required=True,string='Indicador')
    objetivopoa_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',string="Objetivo Operativo",track_visibility=True)
    comentario=fields.Char("Comentario")
    tipo = fields.Selection([('Cualitativo','Cualitativo'),('Cuantitativo','Cuantitativo')],related='resultado_id.tipo')
    valor=fields.Float("Avance del periodo")
    valor_previo=fields.Float("Avance acumulado anterior")
    valor_acumulado=fields.Float("Avance acumulado",compute='_compute_acumulado')
    meta=fields.Float("Meta",related='resultado_id.cantidad')
    report_id=fields.Many2one(comodel_name='fiaes.reporte.plan',string="Reporte",track_visibility=True)
    plan_id = fields.Many2one(comodel_name='fiaes.planunidad',related='report_id.plan_id',required=True)
    fecha = fields.Date(string="Fecha",related='report_id.fecha')
    document = fields.Binary(string="documento",track_visibility=True)
    file_name=fields.Char("file name")
    
    @api.one
    @api.depends('valor','valor_previo')
    def _compute_acumulado(self):
        for r in self:
            r.valor_acumulado=r.valor+r.valor_previo


class report_indicador(models.Model):
    _name='fiaes.reporte.indicador'
    _description='Indicador'
    name = fields.Char(string="Indicador",related='indicador_id.name')
    forma_calculo = fields.Text(string="Calculo",related='indicador_id.forma_calculo')
    poaindicador_id=fields.Many2one(comodel_name='fiaes.poaobjetivos.indicador',required=True,string='Indicador')
    indicador_id=fields.Many2one(comodel_name='fiaes.indicador',required=True,string='Indicador')
    objetivopoa_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',string="Objetivo Operativo",track_visibility=True)
    comentario=fields.Char("Comentario")
    valor=fields.Float("Avance del periodo")
    valor_previo=fields.Float("Avance acumulado anterior")
    valor_acumulado=fields.Float("Avance acumulado",compute='_compute_acumulado')
    meta=fields.Float("Meta",related='poaindicador_id.valor')
    report_id=fields.Many2one(comodel_name='fiaes.reporte.plan',string="Reporte",track_visibility=True)
    plan_id = fields.Many2one(comodel_name='fiaes.planunidad',related='report_id.plan_id',required=True)
    fecha = fields.Date(string="Fecha",related='report_id.fecha')
    
    @api.one
    @api.depends('valor','valor_previo')
    def _compute_acumulado(self):
        for r in self:
            r.valor_acumulado=r.valor+r.valor_previo
            
            

class reportCalculo(models.Model):
    _name = 'fiaes.calculo'
    _description='Calculo de indicadores'
    _inherit= ['mail.thread']
    name = fields.Char(string="Reporte")    
    fecha = fields.Date(string="Fecha",required=True)
    indicador_ids=fields.One2many('fiaes.calculo.indicador','calculo_id',string='Indicadores')
    
    @api.one
    def generate_items(self):
        for r in self:
            #Calculando primero los que no tiene subindicadores
            self.env['fiaes.calculo.indicador'].search([('calculo_id','=',r.id)]).unlink()
            indicadores=self.env['fiaes.indicador'].search([('desagregaciones','=','Fin')])
            dicind={}
            for i in indicadores:
                dicvars={}
                for v in i.variable_ids:
                    previos=self.env['fiaes.reporte.variable'].search(['&',('variable_id','=',v.id),('fecha','<',r.fecha)])
                    total=0.0
                    for p in previos:
                        total=total+p.valor
                    dicvars[v.codigo]=total
                dicvars['meta']=i.valor
                dicvars['lb']=i.lineabase
                valor=float(safe_eval(i.forma_calculo,dicvars))
                dicind[i.nombre_corto]=valor
                dicvars['valor']=valor
                ind=self.env['fiaes.calculo.indicador'].create({'indicador_id':i.id,'valor':valor,'calculo_id':r.id})
                for inter in i.interpretacion_ids:
                    resultado=bool(safe_eval(inter.calculo,dicvars))
                    self.env['fiaes.calculo.interpretacion'].create({'indicador_id':ind.id,'name':inter.name,'calculo':inter.calculo,'resultado':resultado})
            indicadores=self.env['fiaes.indicador'].search([('desagregaciones','=','Indicador')],order="sequence")
            for i in indicadores:
                dicind['meta']=i.valor
                dicind['lb']=i.lineabase
                valor=float(safe_eval(i.forma_calculo,dicind))
                dicind[i.nombre_corto]=valor
                ind=self.env['fiaes.calculo.indicador'].create({'indicador_id':i.id,'valor':valor,'calculo_id':r.id})
                dicind['valor']=valor
                for inter in i.interpretacion_ids:
                    resultado=bool(safe_eval(inter.calculo,dicind))
                    self.env['fiaes.calculo.interpretacion'].create({'indicador_id':ind.id,'name':inter.name,'calculo':inter.calculo,'resultado':resultado})
            
                
            
    
    
class calculo_indicador(models.Model):
    _name='fiaes.calculo.indicador'
    _description='Indicador'
    name = fields.Char(string="Indicador",related='indicador_id.name')
    forma_calculo = fields.Text(string="Calculo",related='indicador_id.forma_calculo')
    indicador_id=fields.Many2one(comodel_name='fiaes.indicador',required=True,string='Indicador')
    comentario=fields.Char("Comentario")
    valor=fields.Float("Avance del periodo")
    meta=fields.Float("Meta",related='indicador_id.valor')
    calculo_id=fields.Many2one(comodel_name='fiaes.calculo_id',string="Calculo",track_visibility=True)
    interpretacion_ids = fields.One2many(comodel_name='fiaes.calculo.interpretacion', inverse_name='indicador_id',track_visibility=True)

class calculo_interpretacion(models.Model):
    _name='fiaes.calculo.interpretacion'
    _description='Interpretacion del indicador'
    name= fields.Char("Interpretacion",track_visibility=True)
    calculo= fields.Char("Condicion",track_visibility=True)
    indicador_id=fields.Many2one(comodel_name='fiaes.calculo.indicador',ondelete='cascade',string="Indicador padre",track_visibility=True)
    resultado=fields.Boolean("Resultado")
    
    
    
    
    
    
    
    
class reportPlan_inversion(models.Model):
    _name = 'fiaes.reporte.inversion'
    _description='Reporte de componente'
    _inherit= ['mail.thread']
    name = fields.Char(string="Reporte",compute='_compute_name')
    inversion_id = fields.Many2one(comodel_name='fiaes.inversion',required=True)
    fecha = fields.Date(string="Fecha",required=True)
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado',required=True,default='Borrador',track_visibility=True)
    variable_ids=fields.One2many('fiaes.reporte.inversion.variable','report_id',string='Variables')
    resultado_ids=fields.One2many('fiaes.reporte.inversion.resultado','report_id',string='Resultados')
    indicador_ids=fields.One2many('fiaes.reporte.inversion.indicador','report_id',string='Indicadores')
    
    @api.one
    def aprobar(self):
        for r in self:
            r.state='Aprobado'
    
    @api.one
    def regresar(self):
        for r in self:
            r.state='Borrador'
    
    @api.one
    def cancelar(self):
        for r in self:
            r.state='Cancelado'

    
    @api.one
    @api.depends('inversion_id','fecha')
    def _compute_name(self):
        for r in self:
            if r.inversion_id:
                if r.fecha:
                    r.name=r.inversion_id.name+' '+r.fecha.strftime("%m/%d/%Y")
    
    @api.one
    def generate_items(self):
        for r in self:
            if r.inversion_id:
                for i in r.indicador_ids:
                    #TODO:crear el indicador
                    dic={}
                    dic["inversion_indicador_id"]=i.id
                    dic["indicador_id"]=i.indicador_id.id
                    dic["valor"]=0.0
                    dic["report_id"]=r.id
                    previo=0.0
                    previos=self.env['fiaes.reporte.inversion.indicador'].search(['&',('inversion_indicador_id','=',i.id),('inversion_id','=',r.inversion_id.id),('report_id','!=',r.id),('fecha','<',r.fecha)])
                    for p in previos:
                        previo=previo+p.valor
                    dic["valor_previo"]=previo
                    existe=self.env['fiaes.reporte.inversion.indicador'].search(['&',('inversion_indicador_id','=',i.id),('report_id','=',r.id)],limit=1)
                    if not existe:
                        self.env['fiaes.reporte.inversion.indicador'].create(dic)
                    for v in i.indicador_id.variable_ids:
                        dic={}
                        dic["variable_id"]=v.id
                        dic["valor"]=0.0
                        dic["report_id"]=r.id
                        previo=0.0
                        previos=self.env['fiaes.reporte.inversion.variable'].search(['&',('variable_id','=',v.id),('inversion_id','=',r.inversion_id.id),('report_id','!=',r.id),('fecha','<',r.fecha)])
                        for p in previos:
                            previo=previo+p.valor
                        dic["valor_previo"]=previo
                        existe=self.env['fiaes.reporte.inversion.variable'].search(['&',('variable_id','=',v.id),('report_id','=',r.id)],limit=1)
                        if not existe:
                            self.env['fiaes.reporte.inversion.variable'].create(dic)
                    for a in o.actividad_line:
                        for re in a.resultados_line:
                            dic={}
                            dic["resultado_id"]=re.id
                            dic["actividad_id"]=o.id
                            dic["valor"]=0.0
                            dic["report_id"]=r.id
                            previo=0.0
                            previos=self.env['fiaes.reporte.inversion.resultado'].search(['&',('resultado_id','=',re.id),('inversion_id','=',r.inversion_id.id),('report_id','!=',r.id),('fecha','<',r.fecha)])
                            for p in previos:
                                previo=previo+p.valor
                            dic["valor_previo"]=previo
                            existe=self.env['fiaes.reporte.inversion.resultado'].search(['&',('resultado_id','=',v.id),('report_id','=',r.id)],limit=1)
                            if not existe:
                                self.env['fiaes.reporte.inversion.resultado'].create(dic)
    @api.one
    def calcular_indicador(self):
        for r in self:
            for i in r.indicador_ids:
                dic={}
                for v in r.variable_ids:
                    if v.indicador_id.id==i.indicador_id.id:
                        dic[v.codigo]=v.valor
                i.valor=float(safe_eval(i.forma_calculo, dic))

class report_variable_inversion(models.Model):
    _name='fiaes.reporte.inversion.variable'
    _description='variable del indicador'
    name = fields.Char(string="variable",related='variable_id.name')
    codigo = fields.Char(string="variable",related='variable_id.codigo')
    variable_id=fields.Many2one(comodel_name='fiaes.indicador.variable',required=True,string='Variable')
    indicador_id=fields.Many2one(comodel_name='fiaes.indicador',related="variable_id.indicador_id",required=True,string='Indicador')
    inversion_id = fields.Many2one(comodel_name='fiaes.inversion',related='report_id.inversion_id',required=True)
    comentario=fields.Char("Comentario")
    valor=fields.Float("Avance del periodo")
    valor_previo=fields.Float("Avance acumulado anterior")
    valor_acumulado=fields.Float("Avance acumulado",compute='_compute_acumulado')
    report_id=fields.Many2one(comodel_name='fiaes.reporte.inversion',string="Reporte",track_visibility=True)
    fecha = fields.Date(string="Fecha",related='report_id.fecha',store=True)
    document = fields.Binary(string="documento",track_visibility=True)
    file_name=fields.Char("file name")
    
    @api.one
    @api.depends('valor','valor_previo')
    def _compute_acumulado(self):
        for r in self:
            r.valor_acumulado=r.valor+r.valor_previo


class report_resultado_inversion(models.Model):
    _name='fiaes.reporte.inversion.resultado'
    _description='Resultados'
    name = fields.Char(string="Resultado",related='resultado_id.name')
    resultado_id=fields.Many2one(comodel_name='fiaes.inversion.actividad.resultado',required=True,string='Variable')
    actividad_id=fields.Many2one(comodel_name='fiaes.inversion.actividad',related='resultado_id.inversion_actividad_id',required=True,string='Indicador')
    inversion_id = fields.Many2one(comodel_name='fiaes.inversion',related='report_id.inversion_id',required=True)
    comentario=fields.Char("Comentario")
    valor=fields.Float("Avance del periodo")
    valor_previo=fields.Float("Avance acumulado anterior")
    valor_acumulado=fields.Float("Avance acumulado",compute='_compute_acumulado')
    meta=fields.Float("Meta",related='resultado_id.cantidad',store=True)
    report_id=fields.Many2one(comodel_name='fiaes.reporte.inversion',string="Reporte",track_visibility=True)
    fecha = fields.Date(string="Fecha",related='report_id.fecha',sotre=True)
    document = fields.Binary(string="documento",track_visibility=True)
    file_name=fields.Char("file name")
    
    @api.one
    @api.depends('valor','valor_previo')
    def _compute_acumulado(self):
        for r in self:
            r.valor_acumulado=r.valor+r.valor_previo

class report_indicador_inversion(models.Model):
    _name='fiaes.reporte.inversion.indicador'
    _description='Indicador'
    name = fields.Char(string="Indicador",related='indicador_id.name')
    forma_calculo = fields.Text(string="Calculo",related='indicador_id.forma_calculo')
    inversion_indicador_id=fields.Many2one(comodel_name='fiaes.inversion.indicador',required=True,string='Indicador')
    indicador_id=fields.Many2one(comodel_name='fiaes.indicador',required=True,string='Indicador')
    comentario=fields.Char("Comentario")
    valor=fields.Float("Avance del periodo")
    valor_previo=fields.Float("Avance acumulado anterior")
    valor_acumulado=fields.Float("Avance acumulado",compute='_compute_acumulado')
    meta=fields.Float("Meta",related='inversion_indicador_id.cantidad',store=False)
    report_id=fields.Many2one(comodel_name='fiaes.reporte.inversion',string="Reporte",track_visibility=True,store=False)
    inversion_id = fields.Many2one(comodel_name='fiaes.inversion',related='report_id.inversion_id',required=True,store=False)
    fecha = fields.Date(string="Fecha",related='report_id.fecha')
    
    @api.one
    @api.depends('valor','valor_previo')
    def _compute_acumulado(self):
        for r in self:
            r.valor_acumulado=r.valor+r.valor_previo
