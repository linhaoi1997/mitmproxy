"""重写auto选择的逻辑，自动将graphql选择为request的第一选项"""

from mitmproxy import contentviews
from mitmproxy.net import http
from mitmproxy.utils import strutils
from mitmproxy.contentviews import base


class ViewAuto(base.View):
    name = "Auto"

    def __call__(self, data, **metadata):
        headers = metadata.get("headers", {})
        flow = metadata.get("flow", None)
        is_graphql = False
        if flow:
            is_graphql = "graphql" in flow.request.pretty_url and headers.get("origin", None)
        ctype = headers.get("content-type")
        if data and ctype:
            ct = http.parse_content_type(ctype) if ctype else None
            ct = "%s/%s" % (ct[0], ct[1])
            if is_graphql:
                return contentviews.get("GraphqlVariables")(data, **metadata)
            if ct in contentviews.content_types_map:
                return contentviews.content_types_map[ct][0](data, **metadata)
            elif strutils.is_xml(data):
                return contentviews.get("XML/HTML")(data, **metadata)
            elif ct.startswith("image/"):
                return contentviews.get("Image")(data, **metadata)
        if metadata.get("query"):
            return contentviews.get("Query")(data, **metadata)
        if data and strutils.is_mostly_bin(data):
            return contentviews.get("Hex")(data)
        if not data:
            return "No content", []
        return contentviews.get("Raw")(data)
