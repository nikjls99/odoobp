from odoo import api, models, _


class SurveySurveyTemplate(models.Model):
    _inherit = "survey.survey"

    @api.model
    def action_load_sample_lead_qualification(self):
        return self.env['survey.survey'].create({
            'survey_type': 'lead_qualification',
            'title': _('Getting to know you'),
            'description_done': _('Thanks for answering!'),
            'progression_mode': 'number',
            'questions_layout': 'page_per_question',
            'question_and_page_ids': [
                (0, 0, {  # survey.question
                    'title': _('What is the size of your company?'),
                    'question_type': 'simple_choice',
                    'constr_mandatory': True,
                    'suggested_answer_ids': [
                        (0, 0, {  # survey.question.answer
                            'value': _('1-10 employees'),
                            'create_lead': False
                        }),
                        (0, 0, {  # survey.question.answer
                            'value': _('11-100 employees'),
                            'create_lead': True
                        }),
                        (0, 0, {  # survey.question.answer
                            'value': _('100+ employees'),
                            'create_lead': False
                        })
                    ]
                }),
                (0, 0, {  # survey.question
                    'title': _('Which of the following best describes your main goal?'),
                    'question_type': 'simple_choice',
                    'constr_mandatory': True,
                    'suggested_answer_ids': [
                        (0, 0, {  # survey.question.answer
                            'value': _('Improving efficiency'),
                            'create_lead': True
                        }),
                        (0, 0, {  # survey.question.answer
                            'value': _('Reducing costs'),
                            'create_lead': False
                        }),
                        (0, 0, {  # survey.question.answer
                            'value': _('Expanding sales'),
                            'create_lead': True
                        })
                    ]
                }),
                (0, 0, {  # survey.question
                    'title': _('Who will make the final decision on this purchase?'),
                    'question_type': 'simple_choice',
                    'constr_mandatory': True,
                    'suggested_answer_ids': [
                        (0, 0, {  # survey.question.answer
                            'value': _('Me'),
                            'create_lead': True
                        }),
                        (0, 0, {  # survey.question.answer
                            'value': _('My Manager/Executive'),
                            'create_lead': True
                        }),
                        (0, 0, {  # survey.question.answer
                            'value': _('A team/committee'),
                            'create_lead': False
                        })
                    ]
                }),
            ]
        }).action_show_sample()
