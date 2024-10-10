# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request, Response
from odoo.tools import date_utils
from urllib import parse

from .clv_settings_provider import ClvSettingsProvider
from .controller_helper_v13 import ControllerHelperV13
from .controller_helper_v14 import ControllerHelperV14
from .controller_helper_v15 import ControllerHelperV15
from .controller_helper_v16 import ControllerHelperV16
from .controller_helper_v17 import ControllerHelperV17
from .inventory import InventoryImpl
from .documents import DocumentImpl
from .tables import TablesImpl
from odoo.release import version_info


class ClvApi(http.Controller):
    """
    Entry point of the Inventory API controller (module).
    It supports Inventory API endpoints
    """

    # implementation of the /inventory endpoints
    _inventory_impl = InventoryImpl()
    # implementation of the /documents endpoints
    _documents_impl = DocumentImpl()
    # implementation of the /tables endpoints
    _tables_impl = TablesImpl()

    # controller's helpers to validate input and output objects/dictionaries
    _controller_helpers = {
        13: ControllerHelperV13(),
        14: ControllerHelperV14(),
        15: ControllerHelperV15(),
        16: ControllerHelperV16(),
        17: ControllerHelperV17()
    }

    def __init__(self):
        """
        Ctor
        """
        major_version_code = version_info[0]
        if not major_version_code in self._controller_helpers:
            RuntimeError('Cleverence Inventory API does not support {} version of odoo.'.format(major_version_code))
        self._controller_helper = self._controller_helpers[major_version_code]

    @http.route('/Auth', type='json', auth="public", methods=['POST'])
    def auth(self, **kw):
        """
        @deprecated
        May be used by alternative authorization call.
        @param kw:
        @return:
        """

        # /Auth endpoint was deprecated due to the fact
        # that on Odoo servers working with multiple databases, the server returns 404 NotFound
        # because public endpoint cannot be resolved in this case.
        # A possible solution could be the server wide module,
        # but it was decided to use authentication via /web/session/authenticate.

        params = self._controller_helper.preprocess_request(request)
        request.session.authenticate(params.get('db'),
                                     params.get('login'),
                                     params.get('password'))

        current_db = request.env.cr.dbname
        if current_db == params.get('db'):
            settings = ClvSettingsProvider(request.env)
            if not settings.warehouse15_connected:
                settings.warehouse15_connected = True

        return {'authResult': 'success'}

    @http.route('/RegisterConnection', type='json', auth="user", methods=['POST'])
    def register_connection(self, **kw):
        settings = ClvSettingsProvider(request.env)
        if not settings.warehouse15_connected:
            settings.warehouse15_connected = True

        return {}

    @http.route('/Inventory/getItems', type='json', auth="user", methods=['POST'])
    def inventory_get_items(self, **kw):
        """
        /Inventory/getItems endpoint implementation. Used to get page of inventory items.
        @param kw:
        @return: Dictionary as described in Inventory API swagger model
        """
        params = self._controller_helper.preprocess_request(request)

        offset = self._controller_helper.convert_int_query_parameter(params.get('offset'), 'offset')
        limit = self._controller_helper.convert_int_query_parameter(params.get('limit'), 'limit')
        request_count = self._controller_helper.convert_bool_query_parameter(params.get('requestCount'), 'requestCount')

        return self._inventory_impl.get_items(http.request.env,
                                              params.get('parentId'),
                                              offset,
                                              limit,
                                              request_count)

    @http.route('/Inventory/getItemsByString', type='json', auth="user", methods=['POST'])
    def inventory_get_items_by_string(self, **kw):
        """
        '/Inventory/getItemsByString' endpoint implementation. Used to search inventory items by string match.
        @param kw:
        @return: Dictionary as described in Inventory API swagger model
        """
        params = self._controller_helper.preprocess_request(request)

        offset = self._controller_helper.convert_int_query_parameter(params.get('offset'), 'offset')
        limit = self._controller_helper.convert_int_query_parameter(params.get('limit'), 'limit')
        request_count = self._controller_helper.convert_bool_query_parameter(params.get('requestCount'), 'requestCount')

        return self._inventory_impl.get_items_by_string(http.request.env,
                                                        params.get('matchString'),
                                                        offset,
                                                        limit,
                                                        request_count)

    @http.route('/Inventory/getItemsByIds', type='json', auth="user", methods=['POST'])
    def inventory_get_items_by_ids(self, **kw):
        """
        '/Inventory/getItemsByIds' endpoint implementation. Used to get inventory items with specified UOM ids.
        @param kw:
        @return: Dictionary as described in Inventory API swagger model
        """
        params = self._controller_helper.preprocess_request(request)
        return self._inventory_impl.get_items_by_ids(http.request.env, params.get('idList'))

    @http.route('/Inventory/getItemsBySearchCode', type='json', auth="user", methods=['POST'])
    def inventory_get_items_by_search_code(self, **kw):
        """
        '/Inventory/getItemsBySearchCode' implementation. Used to search inventory Item by id, marking or barcode.
        @param kw:
        @return: Dictionary as described in Inventory API swagger model
        """
        params = self._controller_helper.preprocess_request(request)
        return self._inventory_impl.get_items_by_search_code(http.request.env,
                                                             params.get('searchMode'),
                                                             params.get('searchData'))

    @http.route('/Documents/getDocumentDescriptions', auth='user', type='json', methods=['POST'])
    def get_documents_desc(self, **kw):
        """
        '/Documents/getDocumentDescriptions' endpoint implementation. Used to get list of document's headers
        @param kw:
        @return: Dictionary as described in Inventory API swagger model
        """
        params = self._controller_helper.preprocess_request(request)

        offset = self._controller_helper.convert_int_query_parameter(params.get('offset'), 'offset')
        limit = self._controller_helper.convert_int_query_parameter(params.get('limit'), 'limit')
        request_count = self._controller_helper.convert_bool_query_parameter(params.get('requestCount'), 'requestCount')

        return self._documents_impl.get_descriptions(http.request.env,
                                                     params.get('documentTypeName'),
                                                     offset,
                                                     limit,
                                                     request_count)

    @http.route('/Documents/getDocument', auth='user', type='json', methods=['POST'])
    def get_document(self, **kw):
        """
        '/Documents/getDocument' endpoint implementation. Used to get full document (with expected and actual lines).
        @param kw:
        @return: Dictionary as described in Inventory API swagger model
        """
        params = self._controller_helper.preprocess_request(request)
        return self._documents_impl.get_document(http.request.env,
                                                 params.get('searchMode'),
                                                 params.get('searchCode'),
                                                 params.get('documentTypeName'))

    @http.route('/Documents/setDocument', auth='user', type='json', methods=['POST'])
    def set_document(self, **kw):
        """
        '/Documents/setDocument' endpoint implementation. Used to process finished document in odoo.
        @param kw:
        """
        params = self._controller_helper.preprocess_request(request)
        return self._documents_impl.set_document(http.request.env, params.get('document'), params.get('deviceInfo'))

    @http.route('/Tables/getTable', auth='user', type='json', methods=['POST'])
    def tables_get_items(self, **kw):
        """
        '/Tables/getTable' endpoint implementation. Used to get table's rows page by query.
        @param kw:
        @return: Dictionary as described in Inventory API swagger model
        """
        params = self._controller_helper.preprocess_request(request)

        offset = self._controller_helper.convert_int_query_parameter(params.get('offset'), 'offset')
        limit = self._controller_helper.convert_int_query_parameter(params.get('limit'), 'limit')
        request_count = self._controller_helper.convert_bool_query_parameter(params.get('requestCount'), 'requestCount')

        return self._tables_impl.get_rows(http.request.env,
                                          params.get('query'),
                                          params.get('deviceInfo'),
                                          offset,
                                          limit,
                                          request_count)
