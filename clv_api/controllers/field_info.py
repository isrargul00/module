from typing import Type, List


class FieldInfo:
    """
    Information about some field existing in odoo and Inventory API models
    """

    def __init__(self, api_name_arg: str, api_type_arg: Type, odoo_name_arg: str, odoo_type_arg: Type, odoo_null_value_equivalent_arg: str = None):
        """
        Initialize the new instance of FieldInfo.
        @param api_name_arg: Inventory API name of the field.
        @param api_type_arg: Inventory API type of the field.
        @param odoo_name_arg: Odoo name of the field.
        @param odoo_type_arg: Odoo type of the field.
        @param odoo_null_value_equivalent_arg:
            The equivalent of null value in Odoo.
            For example, 'id' field usually has int type in Odoo, but in InventoryAPI 'id' field is str.
            To convert expression like this 'Item.Id != null' we need to replace 'null' with '-1'.
        """
        self._api_name = api_name_arg
        self._odoo_name = odoo_name_arg
        self._api_type = api_type_arg
        self._odoo_type = odoo_type_arg
        self._odoo_null_value_equivalent = odoo_null_value_equivalent_arg

    @property
    def api_name(self) -> str:
        """
        Name in Inventory API
        @return:
        """
        return self._api_name

    @api_name.setter
    def api_name_setter(self, value: str):
        """
        Sets Inventory API name
        @param value:
        @return:
        """
        self._api_name = value

    @property
    def odoo_name(self) -> str:
        """
        Name in odoo
        @return:
        """
        return self._odoo_name

    @odoo_name.setter
    def odoo_name_setter(self, value: str):
        """
        Sets name in odoo
        @param value:
        @return:
        """
        self._odoo_name = value

    @property
    def api_type(self) -> Type:
        """
        Type (python) in Inventory API
        @return:
        """
        return self._api_type

    @api_type.setter
    def api_type_setter(self, value: Type):
        """
        Sets Inventory API type
        @param value:
        @return:
        """
        self._api_type = value

    @property
    def odoo_type(self) -> Type:
        """
        Odoo field Type (python)
        @return:
        """
        return self._odoo_type

    @api_type.setter
    def odoo_type_setter(self, value: Type):
        """
        Sets odoo field type
        @param value:
        @return:
        """
        self._odoo_type = value

    @property
    def odoo_null_value_equivalent(self) -> str:
        """
        Returns the equivalent of null value in Odoo.
        """
        return self._odoo_null_value_equivalent

    @odoo_null_value_equivalent.setter
    def odoo_null_value_equivalent(self, value: str):
        """
        Sets the equivalent of null value in Odoo.
        """
        self._odoo_null_value_equivalent = value

    @staticmethod
    def create_api_to_odoo_field_map(fields: List) -> dict:
        """
        Creates dictionary to map Inventory API names to odoo's
        @param fields:
        @return:
        """
        result = {}
        for field_info in fields:
            result[field_info.api_name] = field_info
        return result

    @staticmethod
    def create_odoo_to_api_field_map(fields: List) -> dict:
        """
        Creates dictionary to map odoo names to Inventory API
        @param fields:
        @return:
        """
        result = {}
        for field_info in fields:
            result[field_info.odoo_name] = field_info
        return result

