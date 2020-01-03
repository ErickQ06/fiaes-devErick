# -*- coding: utf-8 -*-

{
    "name": "fiaes",
    "category": '',
    "summary": """
     Mantenimiento fiaes .""",
    "description": """
	   test
    """,
    "sequence": 3,
    "author": "Strategi-k",
    "website": "http://strategi-k.com",
    "version": '12.0.0.4',
    "depends": ['stock','purchase','hr','hr_contract','fleet','project','sale_management','account_asset','survey','maintenance','website','website_form'],
    "data": [
        'views/fiaes.xml'
        ,'views/poa.xml'
        ,'views/cuentas_com.xml'
        ,'views/poa_fondos_report.xml'
        ,'views/poa_models.xml'
        ,'views/poa_fondos.xml'
        ,'views/poa_finanzas.xml'
        ,'views/pei.xml'
        ,'views/catalogos.xml'
        ,'views/templates.xml'
        ,'views/templates_compensaciones.xml'
        ,'views/catalogos_d.xml'
        ,'views/report_plan.xml'
        ,'views/compensacion.xml'
        ,'views/pages_compensacion.xml'
        ,'views/compensaciones_desembolso.xml'
        ,'views/proyecto_fondos.xml'
        ,'views/payment.xml'
        ,'views/report_convenio.xml'
        ,'views/presupuesto.xml'
        ,'views/add_presupuesto.xml'
        ,'views/reasignacion.xml'
        ,'views/report_presupuesto.xml'
        ,'views/report_avance.xml'
        ,'views/fiaes_avance_report.xml'
        ,'security/ir.model.access.csv'
        
    ],
    'qweb': [
        
        ],
    "installable": True,
    "application": True,
    "auto_install": False,

}