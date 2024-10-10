from odoo.api import Environment


class ClvSettingsProvider:
    """
    Util class providing easy access to the values of module settings.
    """

    def __init__(self, env: Environment):
        self._config_params = env['ir.config_parameter'].sudo()

    @property
    def warehouse15_connected(self) -> bool:
        """
        Returns value of 'clv_api.clv_warehouse15_connected' setting.
        """
        return self._get_bool_param('clv_api.clv_warehouse15_connected')

    @warehouse15_connected.setter
    def warehouse15_connected(self, value: bool) -> None:
        self._config_params.set_param('clv_api.clv_warehouse15_connected', value)

    @property
    def default_scan_locations(self) -> bool:
        """
        Returns value of 'clv_api.clv_default_scan_locations' setting.
        """
        return self._get_bool_param('clv_api.clv_default_scan_locations')

    @property
    def allow_only_lowest_level_locations(self) -> bool:
        """
        Returns value of 'clv_api.clv_allow_only_lowest_level_locations' setting.
        """
        return self._get_bool_param('clv_api.clv_allow_only_lowest_level_locations')

    @property
    def auto_create_backorders(self) -> bool:
        """
        Returns value of 'clv_api.clv_auto_create_backorders' setting.
        """
        return self._get_bool_param('clv_api.clv_auto_create_backorders')

    @property
    def use_fake_serials_in_receiving(self) -> bool:
        """
        Returns value of 'clv_api.clv_use_fake_serials_in_receiving' setting.
        """
        return self._get_bool_param('clv_api.clv_use_fake_serials_in_receiving')

    @property
    def ship_expected_actual_lines(self) -> bool:
        """
        Returns value of 'clv_api.clv_ship_expected_actual_lines' setting.
        """
        return self._get_bool_param('clv_api.clv_ship_expected_actual_lines')

    def _get_bool_param(self, param_name: str) -> bool:
        # It's strange but Odoo returns param value as a bool if it is false and as a string if it is true.
        value = self._config_params.get_param(param_name)
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() == 'true'

        return False
