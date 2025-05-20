from odoo import api, fields, models


class SurveySurvey(models.Model):
    _inherit = "survey.survey"

    survey_type = fields.Selection(
        selection_add=[
            ('lead_qualification', 'Lead qualification'),
        ],
        ondelete={
            'lead_qualification': 'set default'
        }
    )
    created_leads = fields.Integer("Leads", compute='_compute_created_leads')

    @api.depends('created_leads', 'title')
    def _compute_created_leads(self):
        for survey in self:
            domain = [("display_name", "ilike", "Survey " + str(self.id) + " Lead")]
            leads = self.env['crm.lead'].search_count(domain)
            survey.created_leads = leads

    @api.depends_context('uid')
    def _compute_allowed_survey_types(self):
        super()._compute_allowed_survey_types()

        for record in self:
            record.allowed_survey_types.append('lead_qualification')

    @api.onchange('survey_type')
    def _onchange_survey_type(self):
        super()._onchange_survey_type()

        if self.survey_type == 'lead_qualification':
            self.write({
                'certification': False,
                'is_time_limited': False,
                'scoring_type': 'no_scoring',
            })

    def action_survey_user_input_leads(self):
        """This method will show the leads created from the current survey"""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        action['domain'] = [("display_name", "ilike", "Survey " + str(self.id) + " Lead")]
        return action
