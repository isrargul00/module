# -*- coding: utf-8 -*-
from odoo import models, fields, http
from odoo.release import version_info

from urllib.parse import urlencode, urljoin


class ResConfigSettings(models.TransientModel):
    """
    To adds some settings to Cleverence API module
    """
    _inherit = 'res.config.settings'

    clv_warehouse15_connected = fields.Boolean(string="Warehouse 15 connected")
    clv_check_connection_failed = fields.Boolean(string="Check connection failed")

    clv_default_scan_locations = fields.Boolean(string="Location Scanning")
    clv_allow_only_lowest_level_locations = fields.Boolean(string="Restrict to Lowest Level Locations Only")
    clv_auto_create_backorders = fields.Boolean(string="Automatic Backorder Document Generation")
    clv_use_fake_serials_in_receiving = fields.Boolean(string="Temporary Serial Numbers")
    clv_ship_expected_actual_lines = fields.Boolean(string="Send Actual Quantities")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        config_params = self.env['ir.config_parameter'].sudo()

        config_params.set_param('clv_api.clv_warehouse15_connected', self.clv_warehouse15_connected)
        config_params.set_param('clv_api.clv_check_connection_failed', self.clv_check_connection_failed)

        config_params.set_param('clv_api.clv_default_scan_locations', self.clv_default_scan_locations)
        config_params.set_param('clv_api.clv_allow_only_lowest_level_locations', self.clv_allow_only_lowest_level_locations)
        config_params.set_param('clv_api.clv_auto_create_backorders', not self.clv_auto_create_backorders)
        config_params.set_param('clv_api.clv_use_fake_serials_in_receiving', self.clv_use_fake_serials_in_receiving)
        config_params.set_param('clv_api.clv_ship_expected_actual_lines', self.clv_ship_expected_actual_lines)

        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config_params = self.env['ir.config_parameter'].sudo()

        warehouse15_connected = False
        if config_params.get_param('clv_api.clv_warehouse15_connected'):
            warehouse15_connected = config_params.get_param('clv_api.clv_warehouse15_connected').lower() == 'true'

        check_connection_failed = False
        if config_params.get_param('clv_api.clv_check_connection_failed'):
            check_connection_failed = config_params.get_param('clv_api.clv_check_connection_failed').lower() == 'true'

        value_scan_locations = config_params.get_param('clv_api.clv_default_scan_locations')
        value_only_lowest_locs = config_params.get_param('clv_api.clv_allow_only_lowest_level_locations')
        auto_backorders_value = not config_params.get_param('clv_api.clv_auto_create_backorders')
        use_fake_serials_value = config_params.get_param('clv_api.clv_use_fake_serials_in_receiving')
        ship_expected_actual_lines_value = config_params.get_param('clv_api.clv_ship_expected_actual_lines')

        res.update(
            clv_warehouse15_connected=warehouse15_connected,
            clv_check_connection_failed=check_connection_failed,
            clv_default_scan_locations=bool(value_scan_locations),
            clv_allow_only_lowest_level_locations=bool(value_only_lowest_locs),
            clv_auto_create_backorders=bool(auto_backorders_value),
            clv_use_fake_serials_in_receiving=bool(use_fake_serials_value),
            clv_ship_expected_actual_lines=bool(ship_expected_actual_lines_value)
        )

        return res

    def check_connection_action(self):
        config_params = self.env['ir.config_parameter'].sudo()

        connected = False
        if config_params.get_param('clv_api.clv_warehouse15_connected'):
            connected = config_params.get_param('clv_api.clv_warehouse15_connected').lower() == 'true'

        config_params.set_param('clv_api.clv_check_connection_failed', not connected)

        self.update({
            'clv_warehouse15_connected': connected,
            'clv_check_connection_failed': not connected
        })

    def create_cleverence_account_action(self):
        base_url = 'https://www.cleverence.com/auth-new/'
        query_params = {'register': 'yes'}

        meta_info = self._get_meta_info(self.env)
        query_params.update(meta_info)
        filtered_query_params = {k: v for k, v in query_params.items() if v is not None}
        url = urljoin(base_url, '?' + urlencode(filtered_query_params))

        return self._open_link_in_new_tab_action(url)

    def login_cleverence_account_action(self):
        base_url = 'https://www.cleverence.com/auth-new/'
        query_params = {}

        meta_info = self._get_meta_info(self.env)
        query_params.update(meta_info)
        filtered_query_params = {k: v for k, v in query_params.items() if v is not None}
        url = urljoin(base_url, '?' + urlencode(filtered_query_params))

        return self._open_link_in_new_tab_action(url)

    def open_video_manuals_link_action(self):
        return self._open_link_in_new_tab_action('https://www.youtube.com/playlist?list=PL7VM7rFldULc2apPqeOknANWe3bw7-_7k')

    def open_technical_support_link_action(self):
        return self._open_link_in_new_tab_action('https://cleverence.atlassian.net/servicedesk/customer/portal/2/user/login?destination=portal%2F2')

    def open_documentation_link_action(self):
        return self._open_link_in_new_tab_action('https://www.cleverence.com/support/category:1780/?utm_source=odoo-module')

    def open_our_contacts_link_action(self):
        return self._open_link_in_new_tab_action('https://www.cleverence.com/contacts/?utm_source=odoo-module')

    def open_cleverence_link_action(self):
        return self._open_link_in_new_tab_action('https://www.cleverence.com/?utm_source=odoo-module')

    def _open_link_in_new_tab_action(self, url: str):
        return {
            'type': 'ir.actions.act_url',
            'name': 'Open Website',
            'url': url,
            'target': 'new',
        }

    def _get_meta_info(self, env):
        cleverence_product_id = 28533
        odoo_version = version_info[0]
        odoo_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
        odoo_db = env.cr.dbname
        odoo_user = env['res.users'].sudo().browse(env.user.id).login

        return {
            'PRODUCT_ID': cleverence_product_id,
            'odoo_version': odoo_version,
            'odoo_url': odoo_url,
            'odoo_db': odoo_db,
            'odoo_user': odoo_user
        }
