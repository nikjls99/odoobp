# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

from odoo.exceptions import ValidationError
from odoo.fields import Domain


class HrIndividualSkillMixin(models.AbstractModel):
    _name = 'hr.individual.skill.mixin'
    _description = "Skill level"
    _order = "skill_type_id, skill_level_id"
    _rec_name = "skill_id"

    _linked_field_name = ''

    skill_id = fields.Many2one('hr.skill', compute='_compute_skill_id', store=True, domain="[('skill_type_id', '=', skill_type_id)]", readonly=False, required=True, ondelete='cascade')
    skill_level_id = fields.Many2one('hr.skill.level', compute='_compute_skill_level_id', domain="[('skill_type_id', '=', skill_type_id)]", store=True, readonly=False, required=True, ondelete='cascade')
    skill_type_id = fields.Many2one('hr.skill.type',
                                    default=lambda self: self.env['hr.skill.type'].search([], limit=1),
                                    required=True, ondelete='cascade')
    level_progress = fields.Integer(related='skill_level_id.level_progress')
    color = fields.Integer(related="skill_type_id.color")
    valid_from = fields.Date(string="Validity Start", default=fields.Date.today())
    valid_to = fields.Date(string="Validity Stop")
    number_of_levels = fields.Integer(related="skill_type_id.number_of_levels")
    is_certification = fields.Boolean(related="skill_type_id.is_certification")  # if is_certification change the model will not trigger the constrains
    display_warning_message = fields.Boolean()

    @api.constrains(lambda self: ['valid_from', 'valid_to', 'skill_id', 'skill_type_id', 'skill_level_id', self._linked_field_name])
    def _check_not_overlapping_regular_skill(self):
        domain = Domain.FALSE

        for individual_skill in self:
            ind_domain = Domain.AND([
                Domain(f"{self._linked_field_name}.id", "=", individual_skill[self._linked_field_name].id),
                Domain("skill_id.id", "=", individual_skill.skill_id.id),
                Domain("id", "!=", individual_skill.id),
            ])

            if individual_skill.is_certification:
                ind_domain = Domain.AND([
                    ind_domain,
                    Domain("skill_level_id.id", "=", individual_skill.skill_level_id.id),
                    Domain('valid_from', '=', individual_skill.valid_from),
                    Domain('valid_to', '=', individual_skill.valid_to),
                ])
            else:
                ind_domain = Domain.AND([
                    ind_domain,
                    Domain('valid_from', '<=', individual_skill.valid_to),
                    Domain.OR([
                        Domain('valid_to', '=', False),
                        Domain('valid_to', '>=', individual_skill.valid_to),
                    ]),
                ])

            domain = Domain.OR([domain, ind_domain])

        if self.env[self._name].search_count(domain, limit=1):
            raise ValidationError(self.env._("At least one of yours new records overlap some existing ones"))

    @api.constrains('valid_from', 'valid_to')
    def _check_date(self):
        for record in self:
            if record.valid_to and record.valid_from > record.valid_to:
                raise ValidationError(self.env._("The stop date can't be earlier than the start date"))

    @api.constrains('skill_id', 'skill_type_id')
    def _check_skill_type(self):
        for record in self:
            if record.skill_id not in record.skill_type_id.skill_ids:
                raise ValidationError(self.env._("The skill %(name)s and skill type %(type)s doesn't match", name=record.skill_id.name, type=record.skill_type_id.name))

    @api.constrains('skill_type_id', 'skill_level_id')
    def _check_skill_level(self):
        for record in self:
            if record.skill_level_id not in record.skill_type_id.skill_level_ids:
                raise ValidationError(self.env._("The skill level %(level)s is not valid for skill type: %(type)s", level=record.skill_level_id.name, type=record.skill_type_id.name))

    #  To reset the validity period if the skill become certified or uncertified
    @api.onchange('is_certification')
    def _onchange_is_certification(self):
        self.valid_from = fields.Date.today()
        if not self.is_certification:
            self.valid_to = False

    @api.depends('skill_type_id')
    def _compute_skill_id(self):
        for record in self:
            if record.skill_type_id:
                record.skill_id = record.skill_type_id.skill_ids[0] if record.skill_type_id.skill_ids else False
            else:
                record.skill_id = False

    @api.depends('skill_id')
    def _compute_skill_level_id(self):
        for record in self:
            if not record.skill_id:
                record.skill_level_id = False
            else:
                skill_levels = record.skill_type_id.skill_level_ids
                record.skill_level_id = skill_levels.filtered('default_level') or skill_levels[0] if skill_levels else False

    @api.depends('skill_id', 'skill_level_id')
    def _compute_display_name(self):
        for individual_skill in self:
            individual_skill.display_name = f"{individual_skill.skill_id.name}: {individual_skill.skill_level_id.name}"

    @api.onchange('valid_to', 'valid_from')
    def _onchange_valid_date(self):
        self.display_warning_message = self.valid_to and self.valid_from and self.valid_to < self.valid_from

    def unlink(self):
        day = fields.Date.today() - relativedelta(days=1)
        to_remove = self.env[self._name]
        to_expire = self.env[self._name]
        for individual_skill in self:
            if individual_skill.valid_from >= day or (individual_skill.valid_to and individual_skill.valid_to <= day):
                to_remove += individual_skill
            else:
                to_expire += individual_skill
        super(HrIndividualSkillMixin, to_remove).unlink()
        to_expire.write({'valid_to': day})
        return True

    def _filter_and_process_vals(self, vals_list):
        seen_skills = set()
        skills_to_archive = self.env[self._name]
        vals_to_return = []

        existing_skills_domain = Domain.AND(
            [
                Domain.OR(
                    [
                        Domain.AND(
                            [
                                Domain(f"{self._linked_field_name}", "=", vals.get(self._linked_field_name, False)),
                                Domain("skill_id", "=", vals.get("skill_id", False)),
                            ]
                        )
                        for vals in vals_list
                    ]
                ),
                Domain.OR(
                    [
                        Domain("valid_to", "=", False),
                        Domain("valid_to", ">=", fields.Date.today()),
                        Domain("is_certification", "=", True),
                    ]
                ),
            ]
        )

        existing_skills = self.search(existing_skills_domain)
        existing_skills_grouped = existing_skills.grouped(lambda skill: (skill[self._linked_field_name].id, skill.skill_id.id))

        existing_certifications = existing_skills.filtered(lambda s: s.is_certification)
        existing_cert_grouped = defaultdict(set)
        for cert in existing_certifications:
            key = (cert[self._linked_field_name].id, cert.skill_id.id)
            existing_cert_grouped[key].add(
                (
                    cert.skill_level_id.id,
                    fields.Date.from_string(cert.valid_from),
                    fields.Date.from_string(cert.valid_to),
                )
            )

        certification_types = set(
            self.env["hr.skill.type"]
            .browse([vals["skill_type_id"] for vals in vals_list])
            .filtered("is_certification")
            .ids
        )

        for vals in vals_list:
            individual_skill_id = vals[self._linked_field_name]
            skill_id = vals["skill_id"]
            skill_type_id = vals["skill_type_id"]
            skill_level_id = vals["skill_level_id"]
            valid_from = fields.Date.from_string(vals.get("valid_from"))
            valid_to = fields.Date.from_string(vals.get("valid_to"))
            is_certificate = skill_type_id in certification_types

            skill_key = (individual_skill_id, skill_id, valid_from, valid_to)

            if skill_key in seen_skills:
                continue
            seen_skills.add(skill_key)

            if is_certificate:
                cert_group_key = (individual_skill_id, skill_id)
                cert_details = (skill_level_id, valid_from, valid_to)
                if cert_details in existing_cert_grouped.get(cert_group_key, set()):
                    continue
            else:
                if existing_skill := existing_skills_grouped.get((individual_skill_id, skill_id)):
                    skills_to_archive += existing_skill

            vals_to_return.append(vals)

        skills_to_archive.unlink()
        return vals_to_return

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = self._filter_and_process_vals(vals_list)
        if vals_list:
            individual_skills = super().create(vals_list)
            return individual_skills
        return self.env[self._name]

    def write(self, vals):
        if not any(key in vals for key in ["skill_type_id", "skill_id", "skill_level_id", self._linked_field_name]):
            return super().write(vals)

        create_vals = []
        for ind_skill in self:
            new_vals = {
                f'{self._linked_field_name}': vals.get(self._linked_field_name, ind_skill[self._linked_field_name].id),
                'skill_id': vals.get('skill_id', ind_skill.skill_id.id),
                'skill_level_id': vals.get('skill_level_id', ind_skill.skill_level_id.id),
                'skill_type_id': vals.get('skill_type_id', ind_skill.skill_type_id.id),
            }
            skill_type = self.env['hr.skill.type'].browse(new_vals['skill_type_id'])
            valid_from = vals.get('valid_from', ind_skill.valid_from if skill_type.is_certification else fields.Date.today())
            valid_to = vals.get('valid_to', ind_skill.valid_to if skill_type.is_certification else False)
            new_vals.update({
                'valid_from': valid_from,
                'valid_to': valid_to,
            })
            create_vals.append(new_vals)
        self.unlink()
        self.create(create_vals)

        return True
