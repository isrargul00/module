from odoo.api import Environment


def post_install_hook(env: Environment):
    """
    Post-installation hook to be executed after the module is installed.
    """
    _set_default_clv_settings(env)


def _set_default_clv_settings(env: Environment):
    config_params = env['ir.config_parameter'].sudo()

    config_params.set_param('clv_api.clv_warehouse15_connected', False)
    config_params.set_param('clv_api.clv_check_connection_failed', False)

    config_params.set_param('clv_api.clv_default_scan_locations', False)
    config_params.set_param('clv_api.clv_allow_only_lowest_level_locations', False)
    config_params.set_param('clv_api.clv_auto_create_backorders', False)
    config_params.set_param('clv_api.clv_use_fake_serials_in_receiving', False)
    config_params.set_param('clv_api.clv_ship_expected_actual_lines', False)
