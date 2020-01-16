from odoo import api, models, fields, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID

class Actividadpoa(models.Model):
    _name = 'fiaes.poaactividad'
    _inherit= ['mail.thread']
    name =  fields.Char(string="Actividad",track_visibility=True)
    descripcion = fields.Text(string="Descripcion",track_visibility=True)   
    proyecto = fields.Many2one(comodel_name='project.project', string="Proyecto")  
    objetivopoa_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',string="Objetivo Operativo",track_visibility=True)
    responsable = fields.Many2many(comodel_name='res.users',string="Responsable",relation="actividad_responsables",track_visibility=True)
    coordina = fields.Many2many(comodel_name='res.users',string="Coodina con",relation="actividad_coordina",track_visibility=True)
    inr_id = fields.Many2one(comodel_name='fiaes.inr', string="INR",compute='compute_inr', track_visibility=True )
    subactividades_line = fields.One2many(comodel_name='fiaes.poasubactividad' , inverse_name='actividad_id')
    insumo_line = fields.One2many(comodel_name='fiaes.insumo', inverse_name='actividad_id') 
    resultados_line = fields.One2many(comodel_name='fiaes.resultado', inverse_name='actividad_id') 
    #objetivo_id = fields.Many2one(comodel_name='fiaes.poaobjetivos', string="Objetivos poa")
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad', string="Plan unidad",store=True)
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Presentado', 'Presentado')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado',default='Borrador',related='planunidad_id.state',track_visibility=True,store=True)
    unidad = fields.Many2one(comodel_name='hr.department',related='planunidad_id.unidad',store=True)
    unidad_planilla = fields.Many2one(comodel_name='hr.department',string="Unidad Planilla")
    unidad_final=fields.Many2one(comodel_name='hr.department',string="Unidad ",compute='calcular_unidad',store=True)
    poa_id=fields.Many2one(comodel_name='fiaes.poa',related='planunidad_id.poa_id',store=True)
    total = fields.Float(string="Total", compute="cant_total")
    prioridad=fields.Integer("Prioridad")
    fecha_inicial=fields.Date("Fecha de inicio")
    fecha_final=fields.Date("Fecha de finalizacion")
    ejecutado=fields.Float("Monto ejecutado",compute="calcular_ejecutado",store=False)
    report_line=fields.One2many(comodel_name='fiaes.reporte.actividad', inverse_name='name_actividad')
    peso = fields.Float("Peso de la actividad")
    porcentaje = fields.Float(string="Porcentaje avance")
    porcentajeAvance = fields.Float(string="Porcentaje de avance",  related = 'reporte.porcentaje', store=False)
    reporte = fields.Many2one(comodel_name='fiaes.reporte.actividad')

    @api.one
    @api.depends('unidad','unidad_planilla')
    def calcular_unidad(self):
        for r in self:
            if r.unidad_planilla:
                r.unidad_final=r.unidad_planilla.id
            else:
                r.unidad_final=r.unidad.id
    
    
    @api.one
    @api.depends('unidad')
    def calcular_ejecutado(self):
        for r in self:
            total=0
            compras=self.env['purchase.order.line'].search([('actividad_id','=',r.id),('state','in',('purchase','done'))])
            for c in compras:
                total=total+c.price_subtotal
            r.ejecutado=total
    
    extemp = fields.Boolean(string="Extemporaneo")
    deshabili = fields.Boolean(string="Habilitado")
    
    @api.constrains('fecha_final')
    def _check_nombre(self):
        for r in self:
            if r.fecha_final<r.fecha_inicial:
                raise ValidationError("La fecha final no puede ser menor que la inicial")
    
    @api.one
    @api.depends('insumo_line')
    def cant_total(self):
        total=0.0
        for r in self:
            for a in r.insumo_line:
                total=total+a.total
            r.total=total
    
    @api.one
    @api.depends('objetivopoa_id','proyecto')
    def compute_inr(self):
        for r in self:
            if r.proyecto:
                inr=self.env['fiaes.inr'].search([('unidad','=',r.unidad.id),('proyecto','=',r.proyecto.id),('poa_id','=',r.poa_id.id)],limit=1)
                if inr:
                    r.inr_id=inr
                else:
                    inr=self.env['fiaes.inr'].create({'unidad':r.unidad.id,'proyecto':r.proyecto.id,'poa_id':r.poa_id.id})
                    r.inr_id=inr
    
    
class Subactividadpoa(models.Model):
    _name = 'fiaes.poasubactividad'
    _inherit= ['mail.thread']
    name =  fields.Char(string="Actividad",track_visibility=True)
    descripcion = fields.Text(string="Descripcion",track_visibility=True)
#    proyecto = fields.Many2one(comodel_name='project.project', string="Proyecto") 
#    objetivopoa_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',string="Objetivo Operativo",track_visibility=True)
    responsable = fields.Many2many(comodel_name='res.users',string="Responsable",track_visibility=True)
#    coordina = fields.Many2many(comodel_name='res.users',string="Coodina con",track_visibility=True)
    actividad_id = fields.Many2one(comodel_name='fiaes.poaactividad')
    unidad = fields.Many2one(comodel_name='hr.department',related='actividad_id.unidad',store=True)
    fecha_inicial=fields.Date("Fecha de inicio")
    fecha_final=fields.Date("Fecha de finalizacion")
    fecha_inicial_a=fields.Date("Fecha de inicio",related="actividad_id.fecha_inicial")
    fecha_final_a=fields.Date("Fecha de finalizacion",related="actividad_id.fecha_final")
    
    
            
            
    @api.one
    def duplicate(self):
        for r in self:
            dic={}
            dic['name']=r.name
            dic['descripcion']=r.descripcion
            dic['actividad_id']=r.actividad_id.id
            if r.fecha_inicial:
                dic['fecha_inicial']=r.fecha_inicial
            if r.fecha_final:
                dic['fecha_final']=r.fecha_final
            if r.responsable:
                dic['responsable']=[[6, False, r.responsable.ids]]
            self.env['fiaes.poasubactividad'].create(dic)
    
    @api.constrains('fecha_inicial')
    def _check_fechainicial(self):
        for r in self:
            if r.fecha_inicial<r.fecha_inicial_a:
                raise ValidationError("La fecha inicial de la subactividad debe estar dentro del rango de fechas de la actividad")
            if r.fecha_inicial>r.fecha_final_a:
                raise ValidationError("La fecha inicial de la subactividad debe estar dentro del rango de fechas de la actividad")
    
    @api.constrains('fecha_final')
    def _check_final(self):
        for r in self:
            if r.fecha_final<r.fecha_inicial_a:
                raise ValidationError("La fecha final  de la subactividad debe estar dentro del rango de fechas de la actividad")
            if r.fecha_final>r.fecha_final_a:
                raise ValidationError("La fecha final  de la subactividad debe estar dentro del rango de fechas de la actividad")
    

class insumo(models.Model):
    _name = 'fiaes.insumo'
    _inherit = ['mail.thread']
    name = fields.Char(string="Bien/Servicio")
    categoria = fields.Many2one(comodel_name='fiaes.insumo.categoria', string='Categorias de insumos')
    actividad_id = fields.Many2one(comodel_name='fiaes.poaactividad')
    preciouni = fields.Float(string="Precio Unitario")
    cantidad = fields.Float(string="Cantidad")
    total = fields.Float(string="Total", compute="cant_total",store=True)
    mes = fields.Selection([('01','Enero'),('02','Febrero'),('03','Marzo'),('04','Abril'),('05','Mayo'),('06','Junio'),('07','Julio'),('08','Agosto'),('09','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')])
    fuente = fields.Many2one(comodel_name='fiaes.fuente', string='Fuente de financiamiento')
    inr_id = fields.Many2one(comodel_name='fiaes.inr',related='actividad_id.inr_id', string="INR", track_visibility=True ,store=True)
    proyecto = fields.Many2one(comodel_name='project.project',related='actividad_id.proyecto', string="Proyecto",store=True)  
    objetivopoa_id = fields.Many2one(comodel_name='fiaes.poaobjetivos',related="actividad_id.objetivopoa_id",string="Objetivo Operativo",track_visibility=True)
    planunidad_id = fields.Many2one(comodel_name='fiaes.planunidad',related='objetivopoa_id.planunidad_id', string="Plan unidad",store=True)
    unidad = fields.Many2one(comodel_name='hr.department',related='planunidad_id.unidad',store=True)
    poa_id = fields.Many2one(comodel_name='fiaes.poa', string="POA",related='planunidad_id.poa_id',store=True)
    anio = fields.Char(string="Año",related='poa_id.anio',store=True)
    cuenta_id = fields.Many2one(comodel_name='account.account', string="Cuenta")
    fecha_inicial=fields.Date("Fecha de inicio")
    fecha_inicial_a=fields.Date("Fecha de inicio",related="actividad_id.fecha_inicial")
    fecha_final_a=fields.Date("Fecha de finalizacion",related="actividad_id.fecha_final")
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Presentado', 'Presentado')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Cancelado', 'Cancelado')]
                                    , string='Estado')
    extemp = fields.Boolean(string="Extemporaneo")
    deshabili = fields.Boolean(string="Habilitado") 
    ejecutado=fields.Boolean(string="Ejecutado")
    report_id=fields.Many2one(string="Reporte de insumos")
    
    
#    @api.one
#    @api.depends('mes')
#    def _create_date(self):
#        for r in self:
#            r.fecha_inicial=datetime.strptime(r.anio+'-'+r.mes+'-01', '%Y-%m-%d').date()
    @api.one
    def duplicate(self):
        for r in self:
            dic={}
            dic['name']=r.name
            dic['categoria']=r.categoria.id
            dic['actividad_id']=r.actividad_id.id
            dic['preciouni']=r.preciouni
            dic['cantidad']=r.cantidad
            dic['mes']=r.mes
            dic['fuente']=r.fuente.id
            dic['unidad']=r.unidad.id
            dic['cuenta_id']=r.cuenta_id.id
            self.env['fiaes.insumo'].create(dic)
            
    
    @api.constrains('mes')
    def _check_mes(self):
        for r in self:
            fecha=datetime.strptime(r.anio+'-'+r.mes+'-01', '%Y-%m-%d').date()
            if r.fecha_inicial_a:
                if fecha<r.fecha_inicial_a:
                    raise ValidationError("El mes debe estar dentro del rango de fechas de la actividad")
                if fecha>r.fecha_final_a:
                    raise ValidationError("El mes debe estar dentro del rango de fechas de la actividad")
    
    @api.constrains('cantidad','preciouni')
    def _check_monto(self):
        for r in self:
            total=r.total
            for o in r.planunidad_id.objetivo_line:
                for a in o.actividad_line:
                    for i in a.insumo_line:
                        if i.id!=r.id:
                            total=total+i.total
            if total>r.planunidad_id.disponible:
                raise ValidationError("El Total disponible para el plan de unidad ha sido excedido")

    

    @api.one
    @api.depends('cantidad','preciouni')
    def cant_total(self):
        for r in self:
            r.total=r.preciouni*r.cantidad

class resultado(models.Model):
    _name = 'fiaes.resultado'
    _inherit = ['mail.thread']
    name = fields.Char(string="Resultado")
    uom_id=fields.Many2one("uom.uom",string="Unidad de medida",track_visibility=True)  
    actividad_id = fields.Many2one(comodel_name='fiaes.poaactividad')
    tipo = fields.Selection([('Cualitativo','Cualitativo'),('Cuantitativo','Cuantitativo')])
    cantidad = fields.Float(string="Meta")
    supuesto = fields.Char(string="Supuesto")
    
class reportePlan(models.Model):
    _name='fiaes.reporteplanunidad'
    _description='reporte de presupuestos por plan de unidad'
    _auto = False

    name=fields.Char('Planunidad')
    refuerzo=fields.Float('Refuerzo')
    recorte=fields.Float('Recorte')
    ejecutado=fields.Float('Ejecutado')
    presupuesto = fields.Float('Presupuesto')
    planunidad_id=fields.Many2one(comodel_name='fiaes.planunidad')

    @api.model_cr  # cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""CREATE OR REPLACE VIEW %s AS
        (SELECT fi.planunidad_id as id, fi.planunidad_id, hd.name as name, sum(fi.total) as presupuesto,
        sum(case fi.extemp when true then  fi.total end)as refuerzo,
        sum(case fi.deshabili when true then fi.total end)as recorte,
        sum(case fi.ejecutado when true then fi.total end)as ejecutado
        FROM fiaes_insumo fi inner join fiaes_planunidad fp
        on fi.planunidad_id=fp.id 
        inner join hr_department hd on fp.unidad=hd.id
        group by fi.planunidad_id, hd.name)
        """% self._table)
    
class reporteProyecto(models.Model):
    _name='fiaes.reporteproyecto'
    _description='reporte de presupuestos por proyecto'
    _auto= False

    name=fields.Char('proyecto')
    refuerzo=fields.Float('refuerzo')
    recorte=fields.Float('ejecutado')
    ejecutado=fields.Float('ejecutado')
    presupuesto = fields.Float('Presupuesto')
    planunidad_id=fields.Many2one(comodel_name='fiaes.planunidad')
    proyecto_id=fields.Many2one(comodel_name='project.project')

    @api.model_cr 
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""
        CREATE OR REPLACE VIEW %s AS
        (SELECT fi.proyecto AS id , fi.proyecto as proyecto_id, fi.planunidad_id as planunidad_id, aa.name AS name, SUM(fi.total) AS presupuesto , 
        SUM(CASE fi.extemp WHEN true THEN fi.total END) AS refuerzo,
        SUM(case fi.deshabili when true then fi.total END) AS recorte,
        SUM(case fi.ejecutado when true then fi.total END) AS ejecutado
        FROM fiaes_insumo fi INNER JOIN fiaes_planunidad fp
        ON fi.planunidad_id=fp.id INNER JOIN project_project aa 
        ON fi.proyecto=aa.id GROUP BY fi.proyecto, aa.name,fi.planunidad_id)
        """% self._table)

class reporteActividad(models.Model):
    _name='fiaes.reporteactividad'
    _description='reporte de presupuestos por actividad'
    _auto = False

    name=fields.Char('planunidad')
    refuerzo=fields.Float('Refuerzo')
    recorte=fields.Float('Recorte')
    ejecutado=fields.Float('Ejecutado')
    presupuesto = fields.Float('Presupuesto')
    planunidad_id=fields.Many2one(comodel_name='fiaes.planunidad')
    actividad_id=fields.Many2one(comodel_name='fiaes.planunidad')

    @api.model_cr  # cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""CREATE OR REPLACE VIEW %s AS
        (SELECT fi.actividad_id AS id, fi.actividad_id AS actividad_id,fi.planunidad_id, aa.name AS Actvidad, aa.name AS name, SUM(fi.total) AS presupuesto , 
        SUM(CASE fi.extemp WHEN true THEN fi.total END) AS refuerzo,
        SUM(CASE fi.deshabili WHEN true THEN fi.total END) AS recorte,
        SUM(CASE fi.ejecutado WHEN true THEN fi.total END) AS ejecutado
        FROM fiaes_insumo fi INNER JOIN fiaes_planunidad fp
        ON fi.planunidad_id=fp.id INNER JOIN fiaes_poaactividad aa 
        ON fi.actividad_id=aa.id GROUP BY fi.actividad_id, aa.name,fi.planunidad_id)
        """% self._table)
