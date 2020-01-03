# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID



class solicitud_registro(models.Model):
    _name='fiaes.compensacion.registro'
    _inherit= ['mail.thread']
    _description= 'Solicitud de registro de usuario'
    name=fields.Char("Nombre")
    telefono=fields.Char("Telefono")
    email=fields.Char("Email")
    nit=fields.Char("NIT")
    state=fields.Selection(selection=[('Solicitado', 'Solicitado')
                                    ,('Contactado', 'Contactado')
                                    ,('Aprobado', 'Aprobado')
                                    ,('Rechazado', 'Rechazado')]
                                    , string='Estado',required=True,default='Solicitado',track_visibility=True)
    tipo=fields.Selection(selection=[('Titular', 'Titular')
                                    ,('Prestador', 'Prestador de servicios')]
                                    , string='Tipo',required=True,default='Titular',track_visibility=True)
    
    @api.one
    def contactar(self):
        for r in self:
            r.state='Contactado'
    
    @api.one
    def aprobar(self):
        for r in self:
            r.state='Aprobado'
            #enviando el correo de confirmacion
            template = self.env.ref('fiaes.compensacion_registro_solicitud_aprobado', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
            usuario=self.env['res.users'].create({'name':r.name,'login':r.email,'email':r.email})
            grupo=self.env.ref('base.group_portal', False)
            if usuario:
                if grupo:
                    usuario.write({'sel_groups_1_9_10': 9 })
#                usuario.action_reset_password()
    
    @api.one
    def rechazar(self):
        for r in self:
            r.state='Rechazado'
            #enviando el correo de confirmacion
            template = self.env.ref('fiaes.compensacion_registro_solicitud_rechazo', False)
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
                
    
    @api.model
    def create(self, values):
        # Override the original create function for the res.partner model
        record = super(solicitud_registro, self).create(values)
        #enviando el correo de confirmacion
        template = self.env.ref('fiaes.compensacion_registro_solicitud_ingreso', False)
        if template:
            self.env['mail.template'].browse(template.id).send_mail(record.id)
        return record