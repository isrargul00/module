from odoo import models, fields, api


class ConnectedDatabaseInfo(models.Model):
    """
    Contains information about connected Cleverence's database.
    """
    _name = 'clv_api.connected_database_info'

    database_name = fields.Char(string="Database Name")
    web_app_url = fields.Char(string="Web App URL")
    database_id = fields.Char(string="Database ID")
    installation_type = fields.Char(string="Installation Type")
    last_data_exchange_time = fields.Datetime(string="Last Data Exchange Time")
    cleverence_user_login = fields.Char(string="Cleverence User Login")
