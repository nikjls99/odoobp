from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestProjectTemplatesTour(HttpCase):
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

    def test_project_templates_tour(self):
        self.start_tour("/odoo", "project_templates_tour", login="admin")
