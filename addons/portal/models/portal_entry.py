from odoo import fields, models


class PortalEntry(models.Model):
    _name = 'portal.entry'
    _description = 'Portal Entry'

    name = fields.Char(string='Title of Section')
    url = fields.Char(string='Target URL')
    description = fields.Text(string='Description of Section')
    image = fields.Binary(string='Image Section')
    placeholder_count = fields.Char(string="Placeholder Count")
    background_color = fields.Char(default='#FFFFFF', string='Background Color')
    # border_radius = fields.Integer(default=0, string='Border Radius', help='Border radius in pixels')
    # boarder_style = fields.Char(default='1px solid #DDD', string='Border Style')
    sequence = fields.Integer(default=10, string='Sequence', help='Order of appearance in the portal')
    is_alert = fields.Boolean(string="Is Alert", default=False)
