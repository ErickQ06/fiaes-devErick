# -*- coding: utf-8 -*-
##############################################################################


from odoo import http
from odoo.http import request

class Registro(http.Controller):
    
    @http.route('/compensacion/success',auth='public',website=True) 
    def exito(self, **kwargs): 
        return request.render('fiaes.success') 
    
    @http.route('/compensacion',auth='public',website=True) 
    def menu(self, **kwargs): 
        return request.render('fiaes.compensacion_menu1')
    
  
    
    @http.route('/compensacion/new_registro',auth='public',website=True) 
    def newregistro(self, **kwargs): 
        return request.render('fiaes.apply') 
    
    @http.route('/compensacion/solicitudes', auth='user', website=True) 
    def titularsolicitudes(self, **kwargs): 
        Checkout = request.env['fiaes.compensacion.solicitud'] 
        checkouts = Checkout.search([('usuario_id','=',request.env.context.get('uid') )]) 
        return request.render( 
            'fiaes.solicitudes',
            {'docs': checkouts}) 
        
    @http.route('/compensacion/procesos', auth='user', website=True) 
    def titularprocesos(self, **kwargs): 
        Checkout = request.env['fiaes.compensacion.proceso'] 
        checkouts = Checkout.search([('usuario_id','=',request.env.context.get('uid') )]) 
        return request.render( 
            'fiaes.procesos2',
            {'docs': checkouts}) 

    @http.route('/compensacion/view_proceso', auth='user', website=True) 
    def viewprocesos(self, **kwargs): 
        ide="0"
        for field_name, field_value in kwargs.items():
            if field_name=='id':
                ide=field_value
        Checkout = request.env['fiaes.compensacion.proceso'] 
        checkouts = Checkout.search([('id','=',ide)],limit=1) 
        titular=request.env['res.partner'].search([('id','=',checkouts.titular_id.id)],limit=1) 
        proyecto=request.env['fiaes.compensacion.proyecto'].search([('id','=',checkouts.proyecto_id.id)],limit=1) 
        plan=request.env['fiaes.compensacion.desembolso.plan'].search([('projecto_id','=',checkouts.proyecto_id.id)],limit=1) 
        return request.render( 
            'fiaes.view_proceso',
            {'doc': checkouts,'titular':titular,'proyecto':proyecto,'plan':plan}) 
    
    
    @http.route('/compensacion/titulares', auth='user', website=True) 
    def titulares(self, **kwargs): 
        Checkout = request.env['res.partner'] 
        checkouts = Checkout.sudo().search([('usuario_id','=',request.env.context.get('uid') ),('tipo','=','Titular')]) 
        return request.render( 
            'fiaes.titulares',
            {'docs': checkouts}) 
    
    @http.route('/compensacion/new_proceso',auth='user',website=True) 
    def newtitular(self, **kwargs):
        Checkout = request.env['res.partner'] 
        checkouts = Checkout.search([('id','=',request.env.context.get('uid'))],limit=1) 
        return request.render( 
            'fiaes.apply_titular',
            {'usuario': checkouts}) 
    
    @http.route('/compensacion/edit_proceso',auth='user',website=True) 
    def edittitular(self, **kwargs):
        ide="0"
        for field_name, field_value in kwargs.items():
            if field_name=='id':
                ide=field_value
        Checkout = request.env['fiaes.compensacion.solicitud'] 
        checkouts = Checkout.search([('id','=',ide)],limit=1) 
        return request.render( 
            'fiaes.apply_titular',
            {'doc': checkouts}) 
    

    @http.route('/compensacion/proyectos2',auth='user',website=True) 
    def proyectos(self, **kwargs):
        Checkout = request.env['fiaes.compensacion.proyecto'] 
        checkouts = Checkout.sudo().search([('titular_id.usuario_id','=',request.env.context.get('uid'))]) 
        return request.render( 
            'fiaes.proyectos',
            {'docs': checkouts}) 
    
    @http.route('/compensacion/new_proyecto',auth='user',website=True) 
    def newproyecto(self, **kwargs):
        return request.render( 
            'fiaes.apply_proyecto') 
    
    
    
    
    
    
    
    
    
    
    #SELECT A UTILIZAR
    @http.route('/fiaes/select/countries', type='http', auth="user", website=True)
    def fiaes_select_country(self, **kwargs):
        return_string = ""
        countries = request.env['res.country'].sudo().search([])
        if countries:
            return_string += "<div class=\"col-md-4 text-md-right\">\n"
            return_string += "  <label class=\"col-form-label\" for=\"representante_nacionalidad\">Nacionalidad del representante</label>\n"
            return_string += "</div>\n"
            return_string += "<div class=\"col-md-8\">\n"
            return_string += "  <select class=\"form-control  o_website_form_input\" id=\"representante_nacionalidad\" name=\"representante_nacionalidad\">\n"
            for country in countries:
                return_string += "    <option value=\"" + str(country.id) + "\">" + country.name + "</option>\n"
            return_string += "  </select>\n"
            return_string += "</div>\n"
        return return_string
    
    @http.route('/fiaes/select/titulares', type='http', auth="user", website=True)
    def fiaes_select_titular(self, **kwargs):
        return_string = ""
        countries = request.env['res.partner'].sudo().search([('usuario_id','=',request.env.context.get('uid') ),('tipo','=','Titular')]) 
        if countries:
            return_string += "<div class=\"col-md-4 text-md-right\">\n"
            return_string += "  <label class=\"col-form-label\" for=\"titular_id\">Titular</label>\n"
            return_string += "</div>\n"
            return_string += "<div class=\"col-md-8\">\n"
            return_string += "  <select class=\"form-control  o_website_form_input\" id=\"titular_id\" name=\"titular_id\">\n"
            for country in countries:
                return_string += "    <option value=\"" + str(country.id) + "\">" + country.name + "</option>\n"
            return_string += "  </select>\n"
            return_string += "</div>\n"
        return return_string
    
    @http.route('/fiaes/select/departamentos', type='http', auth="user", website=True)
    def fiaes_select_departamento(self, **kwargs):
        return_string = ""
        fieldcontrol="departamento_id"
        labelcontrol="Departamento"
        for field_name, field_value in kwargs.items():
            if field_name=='field':
                fieldcontrol=field_value
            if field_name=='label':
                labelcontrol=field_value
        countries = request.env['fiaes.departamento'].sudo().search([])
        if countries:
            return_string += "<div class=\"col-md-4 text-md-right\">\n"
            return_string += "  <label class=\"col-form-label\" for=\""+fieldcontrol+" \">"+labelcontrol+"</label>\n"
            return_string += "</div>\n"
            return_string += "<div class=\"col-md-8\">\n"
            return_string += "  <select class=\"form-control  o_website_form_input\" id=\""+fieldcontrol+"\" name=\""+fieldcontrol+"\">\n"
            for country in countries:
                return_string += "    <option value=\"" + str(country.id) + "\">" + country.name + "</option>\n"
            return_string += "  </select>\n"
            return_string += "</div>\n"
        return return_string
    
    
    @http.route('/fiaes/select/municipios', type='http', auth="public", website=True)
    def fiaes_select_municipio(self, **kwargs):
        return_string = ""
        values = {}
        fieldcontrol="municipio_id"
        labelcontrol="Municipio"
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
            if field_name=='field':
                fieldcontrol=field_value
            if field_name=='label':
                labelcontrol=field_value
        parents = request.env['fiaes.departamento'].sudo().search([('id','=', values['departamentoid']) ],limit=1)
        if parents:
            municipios = request.env['fiaes.municipio'].sudo().search([('departamento','=', parents.id)])
        if municipios:
            return_string += "<div class=\"col-md-4 text-md-right\">\n"
            return_string += "<label class=\"col-form-label\" for=\""+fieldcontrol+"\">"+labelcontrol+"</label>\n"
            return_string += "</div>\n"
            return_string += "<div class=\"col-md-8\">\n"
            return_string += "  <select class=\"form-control  o_website_form_input\" id=\""+fieldcontrol+"\" name=\""+fieldcontrol+"\">\n"
            for municipio in municipios:
                return_string += "    <option value=\"" + str(municipio.id) + "\">" + municipio.name + "</option>\n"
            return_string += "  </select>\n"
            return_string += "</div>\n"
        return return_string
    

        
  
