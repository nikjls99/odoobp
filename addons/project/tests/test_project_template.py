from odoo.addons.project.tests.test_project_base import TestProjectCommon


class TestProjectTemplates(TestProjectCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project_template = cls.env["project.project"].create({
            "name": "Project Template",
            "is_template": True,
        })
        cls.task_inside_template = cls.env["project.task"].create({
            "name": "Task in Project Template",
            "project_id": cls.project_template.id,
        })

    def test_create_from_template(self):
        """
        Creating a project through the action should result in a non template copy
        """
        project = self.project_template.action_create_from_template()
        self.assertFalse(project.is_template, "The created Project should be a normal project and not a template.")
        self.assertFalse(project.partner_id, "The created Project should not have a customer.")

        self.assertEqual(len(project.task_ids), 1, "The tasks of the template should be copied too.")

    def test_copy_template(self):
        """
        A copy of a template should be a template
        """
        copied_template = self.project_template.copy()
        self.assertTrue(copied_template.is_template, "The copy of the template should also be a template.")
        self.assertEqual(len(copied_template.task_ids), 1, "The child of the template should be copied too.")

    def test_revert_template(self):
        """
        A revert of a template should not be a template
        """
        self.project_template.action_undo_convert_to_template()
        self.assertFalse(self.project_template.is_template, "The reverted template should become a normal template.")
