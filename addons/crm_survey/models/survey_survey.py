from odoo import api, fields, models


class SurveySurvey(models.Model):
    _inherit = "survey.survey"

    created_leads = fields.Integer("Leads", compute='_compute_created_leads')

    @api.depends('created_leads', 'title')
    def _compute_created_leads(self):
        for survey in self:
            domain = [("display_name", "ilike", "Survey " + str(self.id) + " Lead")]
            leads = self.env['crm.lead'].search_count(domain)
            survey.created_leads = leads

    def action_survey_user_input_leads(self):
        """This method will show the leads created from the current survey"""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        action['domain'] = [("display_name", "ilike", "Survey " + str(self.id) + " Lead")]
        return action

    def action_survey_user_input_completed(self):
        action = super().action_survey_user_input_completed()
        if self.survey_type == 'survey':
            action.update({
                'domain': [('survey_id.survey_type', '=', 'survey')]
            })
        return action

    def action_survey_user_input(self):
        action = super().action_survey_user_input()
        if self.survey_type == 'survey':
            action.update({
                'domain': [('survey_id.survey_type', '=', 'survey')]
            })
        return action
