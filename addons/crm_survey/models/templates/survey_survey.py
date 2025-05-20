from odoo import api, models, _


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    @api.model
    def action_setup_lead_qualification_template(self, template_key):
        action = self.env['ir.actions.act_window']._for_xml_id('survey.survey_type_action')
        template_values = self.get_survey_type_templates_data(template_key)
        action['res_id'] = self.env['appointment.type'].create(template_values).id
        action['views'] = [[self.env.ref('appointment.appointment_type_view_form').id, 'form']]
        return action

    @api.model
    def get_lead_qualification_templates_data(self):
        return {
            'lead_qualification': {
                'description': _("Create leads when key answers are chosen"),
                'icon': '../../img/survey_sample_lead_qualification.svg',
                'template_key': 'lead_qualification',
                'title': _("Lead Qualification"),
            },
        }
