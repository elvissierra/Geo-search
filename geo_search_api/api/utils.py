from djangorestframework_camel_case.settings import api_settings
from djangorestframework_camel_case.util import camelize

CASE_TYPE_HEADER = "x-case"
CAMEL_CASE_HEADER_VALUE = "camelcase"


class ConfigurableCamelCaseJSONRenderer(
    api_settings.RENDERER_CLASS
):  # pylint: disable=too-few-public-methods
    json_underscoreize = api_settings.JSON_UNDERSCOREIZE

    def render(self, data, *args, **kwargs):
        """Render response in camelcase or snakecase according to headers."""
        x_case_header = args[1]["request"].headers.get(CASE_TYPE_HEADER)
        if x_case_header and x_case_header.lower() == CAMEL_CASE_HEADER_VALUE:
            return super().render(camelize(data, **self.json_underscoreize), *args, **kwargs)
        return super().render(data, *args, **kwargs)
