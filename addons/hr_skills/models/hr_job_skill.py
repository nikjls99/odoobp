# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain


class HrJobSkill(models.Model):
    _name = "hr.job.skill"
    _description = "Skills for job positions"
    _rec_name = "skill_id"
    _order = "skill_level_id"

    job_id = fields.Many2one(comodel_name="hr.job", required=True, index=True, ondelete="cascade")
    skill_id = fields.Many2one(
        comodel_name="hr.skill",
        compute="_compute_skill_id",
        store=True,
        domain="[('skill_type_id', '=', skill_type_id)]",
        readonly=False,
        required=True,
    )
    skill_level_id = fields.Many2one(
        comodel_name="hr.skill.level",
        compute="_compute_skill_level_id",
        domain="[('skill_type_id', '=', skill_type_id)]",
        store=True,
        readonly=False,
        required=True,
    )
    skill_type_id = fields.Many2one(comodel_name="hr.skill.type", required=True)
    level_progress = fields.Integer(related="skill_level_id.level_progress")
    number_of_levels = fields.Integer(related="skill_type_id.number_of_levels")
    is_certification = fields.Boolean(related="skill_type_id.is_certification")
    color = fields.Integer(related="skill_type_id.color")
    valid_from = fields.Date(default=fields.Date.today())
    valid_to = fields.Date()

    @api.constrains("valid_from", "valid_to", "skill_id", "skill_type_id", "skill_level_id", "job_id")
    def _check_not_overlapping_regular_skill(self):
        domain = Domain.FALSE

        for individual_skill in self:
            ind_domain = Domain.AND(
                [
                    Domain("job_id.id", "=", individual_skill.job_id.id),
                    Domain("skill_id.id", "=", individual_skill.skill_id.id),
                    Domain("id", "!=", individual_skill.id),
                ]
            )

            if individual_skill.is_certification:
                ind_domain = Domain.AND(
                    [
                        ind_domain,
                        Domain("skill_level_id.id", "=", individual_skill.skill_level_id.id),
                        Domain("valid_from", "=", individual_skill.valid_from),
                        Domain("valid_to", "=", individual_skill.valid_to),
                    ]
                )
            else:
                ind_domain = Domain.AND(
                    [
                        ind_domain,
                        Domain("valid_from", "<=", individual_skill.valid_to),
                        Domain.OR(
                            [
                                Domain("valid_to", "=", False),
                                Domain("valid_to", ">=", individual_skill.valid_to),
                            ]
                        ),
                    ]
                )

            domain = Domain.OR([domain, ind_domain])

        if self.env["hr.job.skill"].search_count(domain, limit=1):
            raise ValidationError(self.env._("At least one of yours new records overlap some existing ones"))

    @api.constrains("valid_from", "valid_to")
    def _check_date(self):
        for record in self:
            if record.valid_to and record.valid_from > record.valid_to:
                raise ValidationError(self.env._("The stop date can't be earlier than the start date"))

    @api.constrains("skill_id", "skill_type_id")
    def _check_skill_type(self):
        for job_skill in self:
            if job_skill.skill_id not in job_skill.skill_type_id.skill_ids:
                raise ValidationError(
                    self.env._(
                        "The skill %(name)s and skill type %(type)s doesn't match",
                        name=job_skill.skill_id.name,
                        type=job_skill.skill_type_id.name,
                    )
                )

    @api.constrains("skill_type_id", "skill_level_id")
    def _check_skill_level(self):
        for job_skill in self:
            if job_skill.skill_level_id not in job_skill.skill_type_id.skill_level_ids:
                raise ValidationError(
                    self.env._(
                        "The skill level %(level)s is not valid for skill type: %(type)s",
                        level=job_skill.skill_level_id.name,
                        type=job_skill.skill_type_id.name,
                    )
                )

    @api.depends("skill_type_id")
    def _compute_skill_id(self):
        for job_skill in self:
            if job_skill.skill_id.skill_type_id != job_skill.skill_type_id:
                job_skill.skill_id = False

    @api.depends("skill_id")
    def _compute_skill_level_id(self):
        for job_skill in self:
            if not job_skill.skill_id:
                job_skill.skill_level_id = False
            else:
                skill_levels = job_skill.skill_type_id.skill_level_ids
                job_skill.skill_level_id = (
                    skill_levels.filtered("default_level") or skill_levels[0] if skill_levels else False
                )

    @api.onchange("valid_from")
    def _onchange_valid_from(self):
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            self.valid_to = self.valid_from

    @api.onchange("valid_to")
    def _onchange_valid_to(self):
        if self.valid_to and self.valid_from and self.valid_to < self.valid_from:
            self.valid_from = self.valid_to

    @api.depends("skill_id", "skill_level_id")
    def _compute_display_name(self):
        for job_skill in self:
            job_skill.display_name = f"{job_skill.skill_id.name}: {job_skill.skill_level_id.name}"

    def unlink(self):
        """
        A record that was created within the last day should be deleted while records created that should be archived.
        """
        today = fields.Date.today()
        delete_time_threshold = relativedelta(days=1)
        skills_to_delete = self.filtered(lambda s: s.is_certification or s.valid_from + delete_time_threshold > today)
        skills_to_archive = self - skills_to_delete
        if skills_to_archive:
            skills_to_archive.with_context(skills_to_archive=True).write({"valid_to": today - delete_time_threshold})
        if skills_to_delete:
            super(HrJobSkill, skills_to_delete).unlink()
        return True

    def write(self, vals):
        if not self.env.context.get("skills_to_archive"):
            vals_skill_type = self.env["hr.skill.type"].browse(vals.get("skill_type_id"))

            def _get_valid_date(skill, field):
                skill_is_certification = vals_skill_type.is_certification if vals_skill_type else skill.is_certification
                if field == "valid_from":
                    return vals.get("valid_from", skill.valid_from if skill_is_certification else fields.Date.today())
                return vals.get("valid_to", skill.valid_to if skill_is_certification else False)

            new_skill_vals = [
                {
                    "job_id": vals.get("job_id", skill.job_id.id),
                    "skill_id": vals.get("skill_id", skill.skill_id.id),
                    "skill_type_id": vals.get("skill_type_id", skill.skill_type_id.id),
                    "skill_level_id": vals.get("skill_level_id", skill.skill_level_id.id),
                    "valid_from": _get_valid_date(skill, "valid_from"),
                    "valid_to": _get_valid_date(skill, "valid_to"),
                }
                for skill in self
            ]
            self.unlink()
            self.create(new_skill_vals)
            return True
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals = self._filter_and_process_vals(vals_list)
        return super().create(prepared_vals)

    def _filter_and_process_vals(self, vals_list):
        """
        This method handles the distinct constraints for skills and certifications (differentiated by `is_certification`)
        by filtering the values in vals_list and archiving existing skills if needed. The key behaviors are:

        Skills:
        1. Only one active skill per `skill_id` is allowed (e.g., one "English" skill per applicant).
        2. Skills created within the last 24 hours are deleted; older ones are archived.

        Certifications (`is_certification=True`):
        1. Multiple certifications with the same `skill_id` and `level_id` are allowed if their date ranges differ (e.g.,
            "Odoo Certified (2024-01-01 → 2024-12-31)" and "Odoo Certified (2024-06-01 → 2025-05-31)" can coexist.)
        2. Certifications can be deleted at any time.

        Shared Rules:
        - Updates always create new records (archiving old ones) rather than in-place writes.
        - No two records can have all their fields identical.
        - A skill is active if `valid_to` is unset or in the future.
        - A skill that is not active is considered archived

        :returns:  A filtered list of values ready for `create()`
        """
        today = fields.Date.today()
        seen_skills = set()
        skills_to_archive = self.env["hr.job.skill"]
        vals_to_return = []

        existing_skills_domain = Domain.AND(
            [
                Domain.OR(
                    [
                        Domain.AND(
                            [
                                Domain("job_id", "=", vals.get("job_id", False)),
                                Domain("skill_id", "=", vals.get("skill_id", False)),
                            ]
                        )
                        for vals in vals_list
                    ]
                ),
                Domain.OR(
                    [
                        Domain("valid_to", "=", False),
                        Domain("valid_to", ">=", today),
                        Domain("is_certification", "=", True),
                    ]
                ),
            ]
        )

        existing_skills = self.search(existing_skills_domain)
        existing_skills_grouped = existing_skills.grouped(lambda skill: (skill.job_id.id, skill.skill_id.id))

        existing_certifications = existing_skills.filtered(lambda s: s.is_certification)
        existing_cert_grouped = defaultdict(set)
        for cert in existing_certifications:
            key = (cert.job_id.id, cert.skill_id.id)
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
            job_id = vals["job_id"]
            skill_id = vals["skill_id"]
            skill_type_id = vals["skill_type_id"]
            skill_level_id = vals["skill_level_id"]
            valid_from = fields.Date.from_string(vals.get("valid_from"))
            valid_to = fields.Date.from_string(vals.get("valid_to"))
            is_certificate = skill_type_id in certification_types

            skill_key = (job_id, skill_id, valid_from, valid_to)

            if skill_key in seen_skills:
                continue
            seen_skills.add(skill_key)

            if is_certificate:
                cert_group_key = (job_id, skill_id)
                cert_details = (skill_level_id, valid_from, valid_to)
                if cert_details in existing_cert_grouped.get(cert_group_key, set()):
                    continue
            else:
                if existing_skill := existing_skills_grouped.get((job_id, skill_id)):
                    skills_to_archive += existing_skill

            vals_to_return.append(vals)

        skills_to_archive.unlink()
        return vals_to_return
