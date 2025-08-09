{
    'name': 'PGI Helpdesk',
    'version': '18.0.0.1',
    'summary': 'Gestión de tickets de soporte alineado a ITIL para el SLEP Chinchorro',
    'description': """
Este módulo permite registrar, clasificar y gestionar solicitudes e incidentes de soporte técnico
provenientes de usuarios del SLEP, con trazabilidad, historial, y categorización por estado y prioridad.
""",
    'author': 'SLEP Chinchorro - Eduardo Farías',
    'website': 'https://slepchinchorro.cl',
    'category': 'Services/Helpdesk',
    'depends': ['base', 'mail', 'contacts', 'helpdesk_mgmt', 'spreadsheet', 'spreadsheet_dashboard'],
    'data': [
        'security/ir.model.access.csv',
        'data/dashboard_ticket_metrics.xml',
        'views/close_ticket_wizard_view.xml',
        'views/helpdesk_ticket_category_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/res_partner_view.xml',
        'views/helpdesk_ticket_templates.xml',
        'views/assign_technician_wizard_view.xml',
        'views/helpdesk_ticket_stage_view.xml',
        'views/helpdesk_ticket_menus.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pgi_helpdesk/static/src/js/portal_ticket_filter.js',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
