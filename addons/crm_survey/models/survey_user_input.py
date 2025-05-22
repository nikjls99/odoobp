from odoo import models


class SurveyUser_Input(models.Model):
    _inherit = "survey.user_input"

    def _mark_done(self):
        super()._mark_done()

        # Generate lead
        self._generate_lead()

    def _generate_lead(self):
        """ This method will :
        - generate an new opportuniy
        - leak that to the current survey
        """
        is_lead_answer = False
        public_user_mail = None
        description = "Question answers:"
        for user_input in self:
            current_question = None
            first_answer = True
            for answer_id in user_input.user_input_line_ids:
                ### Write the lead description (in HTML format)
                # Write question to the description
                question = answer_id.question_id.title
                if question != current_question:
                    if description:
                        description += "<br/>&emsp;- "
                    current_question = question
                    first_answer = True
                    description += current_question

                # Write answer(s) to the question
                answer = answer_id._get_answer_value()
                if answer is not None:
                    if first_answer:
                        description += ' ' + str(answer)
                        first_answer = False
                    else:
                        description += ', ' + str(answer)
                else:
                    description += "<i> Skipped</i>"

                # Check if answer should create a lead
                if answer_id.suggested_answer_id:
                    if answer_id.suggested_answer_id.create_lead and not is_lead_answer:
                        is_lead_answer = True

                # Check if the question has a email answer
                if answer_id.question_id.validation_email:
                    public_user_mail = answer

            ### Generate the lead
            if is_lead_answer:
                medium = self.env['utm.medium']._fetch_or_create_utm_medium('Survey')

                source = self.env['utm.source'].search([('name', '=', self.survey_id.title)])
                if not source:
                    source = self.env['utm.source'].create({
                                'name': self.survey_id.title,
                            })

                # Check if the suvey responsible is from a sales team
                survey_responsible = user_input.survey_id.user_id
                if survey_responsible:
                    is_survey_responsible_in_sales_team = self.env['crm.team'].search([('member_ids', 'in', survey_responsible.id)])
                    if is_survey_responsible_in_sales_team:
                        survey_responsible = survey_responsible.id
                    else:
                        survey_responsible = False
                else:
                    survey_responsible = False

                dico = {
                    'name': 'Survey ' + str(self.survey_id.id) + ' Lead - ' + self.survey_id.title,
                    'user_id': survey_responsible,
                    'medium_id': medium.id,
                    'source_id': source.id,
                    'description': description,
                    'type': 'lead',
                }

                if user_input.partner_id.id:  # Check if the person is connected
                    dico['partner_id'] = user_input.partner_id.id
                    self.env['crm.lead'].create(dico)
                else:  # Creation with Odoobot and email field answer otherwise
                    dico['email_from'] = public_user_mail
                    odoobot = self.env.ref('base.user_root')
                    self.env['crm.lead'].with_user(odoobot).create(dico)
