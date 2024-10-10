class DocumentsUtils:
    """
    Provides util methods for Inventory API documents processing.
    """
    @staticmethod
    def extract_business_process_settings(doc):
        """
        Extracts business process settings from document to dictionary,
        where key is 'settingName' and value is 'settingValue'.
        """
        result = {}

        if doc and doc.get('businessProcessSettings'):
            settings = doc.get('businessProcessSettings')
            for setting in settings:
                key = setting.get('settingName')
                if not key:
                    raise RuntimeError('Value of \'settingName\' is null or empty')

                value = setting.get('settingValue')

                if key in result:
                    raise RuntimeError(f'Business process setting with name \'{key}\' is duplicated')

                result[key] = value

        return result
