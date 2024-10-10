from odoo.api import Environment


def pre_uninstall_hook(env: Environment):
    """
    Pre-uninstallation hook to be executed before the module is uninstalled.
    """
    _unlink_clv_settings(env)


def _unlink_clv_settings(env: Environment):
    config_params = env['ir.config_parameter'].sudo()

    config_params.search([('key', '=', 'clv_api.clv_warehouse15_connected')]).unlink()
    config_params.search([('key', '=', 'clv_api.clv_check_connection_failed')]).unlink()

    config_params.search([('key', '=', 'clv_api.clv_default_scan_locations')]).unlink()
    config_params.search([('key', '=', 'clv_api.clv_allow_only_lowest_level_locations')]).unlink()
    config_params.search([('key', '=', 'clv_api.clv_auto_create_backorders')]).unlink()
    config_params.search([('key', '=', 'clv_api.clv_use_fake_serials_in_receiving')]).unlink()
    config_params.search([('key', '=', 'clv_api.clv_ship_expected_actual_lines')]).unlink()
