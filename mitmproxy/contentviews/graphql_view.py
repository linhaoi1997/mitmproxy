"""
for graphql view query
"""
import json
import re

from mitmproxy import contentviews
from beeprint import pp
from mitmproxy.contentviews import base


def double_space(match_obj):
    return match_obj.group(1) * 2


class ViewGraphqlQuery(base.View):
    """查看graphql的query"""
    name = "GraphqlQuery"
    content_types = ["text/plain"]

    def __call__(self, data, **metadata) -> base.TViewResult:
        query = json.loads(data).get("query")
        query = re.sub("( +)", double_space, query)

        return "graphql query", base.format_text(query)


class ViewGraphqlVariables(base.View):
    """查看graphql的varibales"""
    name = "GraphqlVariables"
    content_types = ["text/plain"]

    def __call__(self, data, **metadata) -> base.TViewResult:
        query = json.loads(data).get("query").split("\n")[0].rstrip(" {")
        variables = pp(json.loads(data).get("variables"), output=False)

        def result():
            yield from base.format_text(query)
            yield from base.format_text("variables: \n")
            yield from base.format_text(variables)

        return "graphql variables", result()
