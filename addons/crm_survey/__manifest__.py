# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Lead from Survey',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Generate lead from Lead qualification in Survey',
    'description': """
    It's a bridge between CRM and survey.
    It creates a new survey type: Lead qualification.
    It allows to create a survey with lead-generating answers for questions with suggested answers.
    If, at least, one answer of that has been chosen by the user, a lead is generated.
    """,
    'depends': ['crm',
                'survey',
    ],
    'data': [
        # 'security/ir.model.access.csv',  # TODO rros Security, to see
        'views/survey_question_views.xml',
        'views/survey_survey_views.xml',
        'views/survey_user_views.xml',
    ],
    'auto_install': True,
    'author': 'Odoo S.A.',
    'license': 'LGPL-3',
}
