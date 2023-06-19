"""
Dev notes:
- parsing "linkTo":
    - example: https://www.encodeproject.org/profiles/experiment?format=json&frame=object
        "biosample_ontology": {
            "type": "string",
            "linkTo": "BiosampleType"
        },
    - example: https://www.encodeproject.org/profiles/replicate?format=json&frame=object
        "experiment": {
            "type": "string",
            "linkTo": [
                "Experiment",
                "FunctionalCharacterizationExperiment",
                "SingleCellUnit"
            ]
        },

- parsing "linkFrom":
    - example: https://www.encodeproject.org/profiles/experiment?format=json&frame=object
        "replicates": {
            "type": "array",
            "items": {
                "type": [
                    "string",
                    "object"
                ],
                "linkFrom": "Replicate.experiment"
            }
        },
"""
import json
import os
import logging

from collections import defaultdict
from igvf_minidb.connection import get


logger = logging.getLogger(__name__)


class Profile:
    def __init__(self, name, schema_json):
        """
        Args:
            name:
                Name of a profile in CamelCase (e.g. MouseDonor)
            schema_json:
                Schema JSON

        Properties:
            linked profiles:
                dict of {property_name: profile}
            meta_objs:
                dict of {uuid: metadata object}
        """
        self.name = name
        self.schema_json = schema_json
        self.linked_profiles = {}
        self.meta_objs = {}

    def link_profile(self, property_name, profile):
        self.linked_profiles[property_name] = profile

    def add_meta_obj(self, meta_obj):
        """
        Add metadata object to self and then recursively add metadata object for
        linked profiles too.
        """
        if meta_obj["uuid"] in self.meta_objs:
            logger.info("Found cyclic loop. halting DFS...")
            return

        self.meta_objs[meta_obj["uuid"]] = meta_obj

        for prop, linked_profile in self.linked_profiles.items():
            if prop not in meta_obj:
                continue

            if isinstance(meta_obj[prop], str):
                url_query = meta_obj[prop]
                linked_profile.add_meta_obj(get(url_query))

            elif isinstance(meta_obj[prop], list):
                for url_query in meta_obj[prop]:
                    linked_profile.add_meta_obj(get(url_query))


    def find_linked_profiles(self):
        """
        Find linked profiles in self's properties.

        Return:
            Generator of a list of tuple (property_name, profile_name)

        Notes:
            Profile's name in schema JSON is in CamelCase.
            It's converted to snake_case when being returned.
        """
        for prop_name, prop in self.schema_json["properties"].items():

            linkTo = None
            if prop["type"] == "string":
                if "linkTo" in prop:
                    linkTo = prop["linkTo"]
                    logger.info(f"Found profile linkTo (string): {self.name} to {linkTo}")

            elif prop["type"] == "array" and prop["items"]["type"] == "string":
                if "linkTo" in prop["items"]:
                    linkTo = prop["items"]["linkTo"]
                    logger.info(f"Found profile linkTo (array): {self.name} to {linkTo}")

            # to check orphaned meta obj later
            # elif prop["type"] == "array" and prop["items"]["type"] == ["string", "object"]:
            #     if "linkFrom" in prop["items"]:
            #         linkFrom = to_upper_camel_case(
            #             prop["items"]["linkFrom"].split["."][0]
            #         )
            #         logger.info(f"Found profile linkFrom (array): {self.name} from {linkFrom}")
            #         yield prop_name, linkFrom, "from"

            if linkTo:
                if isinstance(linkTo, str):
                    yield prop_name, linkTo
                elif isinstance(linkTo, list):
                    for item in linkTo:
                        yield prop_name, item
                else:
                    raise ValueError("linkTo should be either string of list of string.")


class Profiles:
    def __init__(self, profiles):
        """
        Args:
            profiles:
                Dict of {profile name: Profile object}.
        """
        self.profiles = profiles

    @classmethod
    def load_from_profiles_json_file(cls, profiles_json_file):
        with open(profiles_json_file) as fp:
            profile_schemas = json.load(fp)

        profiles = {}
        for profile_name, schema in profile_schemas.items():
            if profile_name.startswith(("_", "@")):
                continue
            profiles[profile_name] = Profile(profile_name, schema)

        return Profiles(profiles)

    def link_all_profiles(self):

        # check if there are missing profiles (e.g. Dataset)
        profiles_added_on_demand = []

        # find missing profiles first
        for name, profile in self.profiles.items():
            for prop_name, linked_profile_name in profile.find_linked_profiles():

                if linked_profile_name not in self.profiles:
                    # some profiles are missing in all_profiles.json file
                    # send query to portal on demand
                    url_query = f"profiles/{linked_profile_name}"
                    profile = Profile(linked_profile_name, get(url_query))
                    profiles_added_on_demand.append(profile)

        # add missing profiles
        for profile in profiles_added_on_demand:
            self.profiles[profile.name] = profile

        # now start linking profiles
        for name, profile in self.profiles.items():
            for prop_name, linked_profile_name in profile.find_linked_profiles():
                linked_profile = self.profiles[linked_profile_name]
                profile.link_profile(prop_name, linked_profile)

    def print_tree(self, hideEmptyProfile=False):       
        # for profile_name, profile in self.profiles.items():
        for profile_name, profile in sorted(
            self.profiles.items(), key=lambda item: len(item[1].meta_objs)
        ):
            if hideEmptyProfile and len(profile.meta_objs) == 0:
                continue
            print(profile_name, len(profile.meta_objs))
            for prop, linked_profile in profile.linked_profiles.items():
                print("\t", prop, linked_profile.name)
