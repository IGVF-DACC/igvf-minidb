import json
from igvf_minidb.connection import get_meta_obj


class MetaObj:
    def __init__(self, meta_obj, profile):
        self.meta_obj = meta_obj
        self.profile = profile

    def traverse(self):
        for prop_name, linked_profile in self.profile.linked_profiles:
            value = meta_obj[prop_name]

            if isinstance(value, list):
                url_queries = value
            elif ininstance(value, str):
                url_queries = [value]
            else:
                raise ValueError("Meta obj property must be list or string.")

            for url_query in url_queries:
                meta_obj = get_meta_obj(get_meta_obj)
                yield prop_name, meta_obj

class MetaObjs:
    pass
