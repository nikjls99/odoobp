# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ast import literal_eval

from odoo import fields, models, Command, api


class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    applicant_skill_ids = fields.One2many("hr.applicant.skill", "applicant_id", string="Skills", copy=True)
    current_applicant_skill_ids = fields.One2many(
        "hr.applicant.skill",
        "applicant_id",
        string="Valid Skills",
        copy=False,
        compute="_compute_current_applicant_skills",
        readonly=False,
    )
    skill_ids = fields.Many2many("hr.skill", compute="_compute_skill_ids", store=True)
    matching_skill_ids = fields.Many2many(
        comodel_name="hr.skill",
        string="Matching Skills",
        compute="_compute_matching_skill_ids",
    )
    missing_skill_ids = fields.Many2many(
        comodel_name="hr.skill",
        string="Missing Skills",
        compute="_compute_matching_skill_ids",
    )
    matching_score = fields.Integer(string="Matching Score", compute="_compute_matching_skill_ids")

    @api.depends("applicant_skill_ids.skill_id")
    def _compute_skill_ids(self):
        for applicant in self:
            applicant.skill_ids = applicant.applicant_skill_ids.skill_id

    @api.depends("applicant_skill_ids")
    def _compute_current_applicant_skills(self):
        for applicant in self:
            applicant.current_applicant_skill_ids = applicant.applicant_skill_ids.filtered(
                lambda AS: not AS.valid_to or AS.valid_to >= fields.Date.today()
            )

    @api.depends_context("matching_job_id")
    @api.depends("current_applicant_skill_ids", "type_id", "job_id", "job_id.job_skill_ids", "job_id.expected_degree")
    def _compute_matching_skill_ids(self):
        # TODO: The context seems to persist a bit too much
        # When clicking 'Search Matching Applicant' on a job, "matching_job_id" is filled with the id of the job position.
        matching_job_id = self.env.context.get("matching_job_id")
        matching_job = self.env["hr.job"].browse(matching_job_id)
        for applicant in self:
            job = matching_job if matching_job else applicant.job_id
            if job and (job.job_skill_ids or job.expected_degree):
                job_skills = job.job_skill_ids
                job_degree = job.expected_degree.score * 100
                job_total = sum(job_skills.mapped("level_progress")) + job_degree
                job_skill_map = {js.skill_id: js.level_progress for js in job_skills}

                matching_applicant_skills = applicant.current_applicant_skill_ids.filtered(
                    lambda a: a.skill_id in job_skill_map
                )
                applicant_degree = applicant.type_id.score * 100 if job_degree > 1 else 0
                applicant_total = (
                    sum(
                        min(skill.level_progress, job_skill_map[skill.skill_id] * 2)
                        for skill in matching_applicant_skills
                    )
                    + applicant_degree
                )

                matching_skill_ids = matching_applicant_skills.mapped("skill_id")
                missing_skill_ids = job_skills.mapped("skill_id") - matching_applicant_skills.mapped("skill_id")
                matching_score = round(applicant_total / job_total * 100)

                applicant.matching_skill_ids = matching_skill_ids
                applicant.missing_skill_ids = missing_skill_ids
                applicant.matching_score = matching_score
            else:
                applicant.matching_skill_ids = False
                applicant.missing_skill_ids = False
                applicant.matching_score = False

    def _get_employee_create_vals(self):
        vals = super()._get_employee_create_vals()
        vals["employee_skill_ids"] = [
            (
                0,
                0,
                {
                    "skill_id": applicant_skill.skill_id.id,
                    "skill_level_id": applicant_skill.skill_level_id.id,
                    "skill_type_id": applicant_skill.skill_type_id.id,
                },
            )
            for applicant_skill in self.applicant_skill_ids
        ]
        return vals

    def _map_applicant_skill_ids_to_talent_skill_ids(self, vals):
        """
        The applicant_skills_ids contains a list of ORM tuples i.e (command, record ID, {values})
        The challenge lies in the uniqueness of the record ID in this tuple. Each skill (e.g., 'arabic')
        has a distinct ID per applicant, i.e arabic in applicant 1 will have a different id from arabic in
        applicant 2. This means the content of applicant_skills_ids is unique for each record and attempting
        to pass it directly (e.g., applicant.pool_applicant_id.write(vals)) won't yield results so we must
        update each tuple to have the correct command and record ID for the talent pool applicant

        Returns:
            returns a list of create/update/delete commands with skill_ids relevant to the pool_applicant
        """
        applicant_skills = {a.id: a.skill_id.id for a in self.applicant_skill_ids}
        applicant_skills_type = {a.id: a.skill_type_id.id for a in self.applicant_skill_ids}
        talent_skills = {a.skill_id.id: a.id for a in self.pool_applicant_id.applicant_skill_ids}
        translated_skills = []
        for skill in vals["applicant_skill_ids"]:
            command = skill[0]
            record_id = skill[1]
            if command == 0:
                values = skill[2]
                if values["skill_id"] in talent_skills:
                    translated_skill = Command.update(
                        talent_skills[values["skill_id"]],
                        {"skill_level_id": values["skill_level_id"]},
                    )
                    translated_skills.append(translated_skill)
                else:
                    translated_skills.append(skill)
            elif command == 1:
                values = skill[2]
                if applicant_skills[record_id] in talent_skills:
                    translated_skill = Command.update(talent_skills[applicant_skills[record_id]], values)
                    translated_skills.append(translated_skill)
                else:
                    translated_skill = Command.create(
                        {
                            "skill_id": applicant_skills[record_id],
                            "skill_type_id": applicant_skills_type[record_id],
                            "skill_level_id": values["skill_level_id"],
                        }
                    )
                    translated_skills.append(translated_skill)
            elif command == 2:
                if applicant_skills[record_id] in talent_skills:
                    translated_skill = Command.delete(talent_skills[applicant_skills[record_id]])
                    translated_skills.append(translated_skill)
        return translated_skills

    def action_add_to_job(self):
        self.with_context(just_moved=True).write(
            {
                "job_id": self.env["hr.job"].browse(self.env.context.get("matching_job_id")).id,
                "stage_id": self.env.ref("hr_recruitment.stage_job0").id,
            }
        )
        action = self.env["ir.actions.actions"]._for_xml_id("hr_recruitment.action_hr_job_applications")
        action["context"] = literal_eval(action["context"].replace("active_id", str(self.job_id.id)))
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "current_applicant_skill_ids" in vals:
                vals["applicant_skill_ids"] = vals.pop("current_applicant_skill_ids")
        return super().create(vals_list)

    def write(self, vals):
        if "current_applicant_skill_ids" in vals:
            vals["applicant_skill_ids"] = vals.pop("current_applicant_skill_ids")
        if "applicant_skill_ids" in vals:
            for applicant in self:
                if applicant.pool_applicant_id and (not applicant.is_pool_applicant):
                    translated_skills = applicant._map_applicant_skill_ids_to_talent_skill_ids(vals)
                    applicant.pool_applicant_id.write({"applicant_skill_ids": translated_skills})
        return super().write(vals)
