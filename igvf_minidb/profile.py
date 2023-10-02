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
from igvf_minidb.subsampling import Subsampling


logger = logging.getLogger(__name__)


class Profile:
    """Log per every `META_OBJS_PER_LOG` meta objs.
    """
    META_OBJS_PER_LOG = 100

    def __init__(self, name, profile_json, subsampling_json):
        """
        Args:
            name:
                Name of a profile in CamelCase (e.g. MouseDonor)
            profile_json:
                Profile schema JSON
            subsampling_json:
                List of subsampling definition JSONs

        Properties:
            linked profiles:
                dict of {property_name: profile}
            meta_objs:
                dict of {uuid: metadata object}
        """
        logger.info(f"Creating Profile for {name}")
        self.name = name
        self.profile_json = profile_json
        self.linked_profiles = {}
        self.meta_objs = {}
        self._init_subsampling(subsampling_json)

    def link_profile(self, property_name, profile):
        self.linked_profiles[property_name] = profile

    def subsample(self):
        logger.info(f"Start subsampling for profile {self.name}")
        result = []
        for subsampling in self.subsamplings:
            for uuid in subsampling.subsample():
                self.add_meta_obj_uuid(uuid)

    def add_meta_obj_uuid(self, uuid, depth=0, parent_uuids=()):
        url_query = f"{self.name}/{uuid}"
        meta_obj = get(url_query + "?format=json&frame=object")
        self.add_meta_obj(meta_obj, depth=depth, parent_uuids=parent_uuids)

    def add_meta_obj(self, meta_obj, depth=0, parent_uuids=()):
        """
        Add metadata object to self and then recursively add metadata object for
        linked profiles too.

        parent_uuids is used to track and avoid cyclic references.
        """
        uuid = meta_obj["uuid"]
        if uuid in self.meta_objs:
            return

        if uuid in parent_uuids:
            logger.info(f"Cyclic ref found. {depth}: {self.name}, {meta_obj['uuid']}")
            return

        parent_uuids += (uuid,)

        self.meta_objs[uuid] = meta_obj

        if depth > 300:
            logger.info(f"Search tree is too deep. {depth}: {self.name}, {meta_obj['uuid']}")

        if len(self.meta_objs) % Profile.META_OBJS_PER_LOG == 0:
            logger.info(f"{len(self.meta_objs)} meta objs added to Profile {self.name} so far")

        for prop, linked_profile in self.linked_profiles.items():
            if prop not in meta_obj:
                continue

            if isinstance(meta_obj[prop], str):
                url_query = meta_obj[prop]
                # logger.info(f"S-Adding {url_query} to Profile {self.name}")
                linked_profile.add_meta_obj(get(url_query + "?format=json&frame=object"), depth=depth + 1, parent_uuids=parent_uuids)

            elif isinstance(meta_obj[prop], list):
                for url_query in meta_obj[prop]:
                    # logger.info(f"L-Adding {url_query} to Profile {self.name}")
                    linked_profile.add_meta_obj(get(url_query + "?format=json&frame=object"), depth=depth + 1, parent_uuids=parent_uuids)

    def find_linked_profiles(self):
        """
        Find linked profiles in self's properties.

        Return:
            Generator of a list of tuple (property_name, profile_name)

        Notes:
            Profile's name in schema JSON is in CamelCase.
            It's converted to snake_case when being returned.
        """
        for prop_name, prop in self.profile_json["properties"].items():

            linkTo = None
            if prop["type"] == "string":
                if "linkTo" in prop:
                    linkTo = prop["linkTo"]
                    logger.info(f"Found profile linkTo (string): {self.name} to {linkTo}")

            elif prop["type"] == "array" and prop["items"]["type"] == "string":
                if "linkTo" in prop["items"]:
                    linkTo = prop["items"]["linkTo"]
                    logger.info(f"Found profile linkTo (array): {self.name} to {linkTo}")

            if linkTo:
                if isinstance(linkTo, str):
                    yield prop_name, linkTo
                elif isinstance(linkTo, list):
                    for item in linkTo:
                        yield prop_name, item
                else:
                    raise ValueError("linkTo should be either string of list of string.")

    def _init_subsampling(self, subsampling_json):
        self.subsamplings = []

        if not subsampling_json:
            return

        for subsampling in subsampling_json:
            self.subsamplings.append(
                Subsampling(
                    profile_name=self.name,
                    search_parameters=subsampling.get("search_parameters"),
                    subsampling_rate=subsampling.get("subsampling_rate"),
                    subsampling_min=subsampling.get("subsampling_min"),
                )
            )


class Profiles:
    def __init__(self, profiles_json, all_subsampling_json):
        """
        Args:
            profiles:
                Dict of {profile name: Profile object}.
        """
        self.profiles = {}
        self.all_subsampling_json = all_subsampling_json

        for profile_name, schema in profiles_json.items():
            if profile_name.startswith(("_", "@")):
                continue
            self.profiles[profile_name] = Profile(
                name=profile_name,
                profile_json=schema,
                subsampling_json=self.all_subsampling_json.get(profile_name)
            )

    def link_all_profiles(self):
        # check if there are missing profiles (e.g. Dataset)
        profiles_added_on_demand = []

        # find missing profiles first
        for name, profile in self.profiles.items():
            for prop_name, linked_profile_name in profile.find_linked_profiles():

                if linked_profile_name not in self.profiles:
                    # some profiles are missing in all_profiles.json file
                    # send query to portal on demand
                    url_query = f"profiles/{linked_profile_name}/?format=json&frame=object"
                    profile = Profile(
                        name=linked_profile_name,
                        profile_json=get(url_query),
                        subsampling_json=self.all_subsampling_json.get(linked_profile_name)
                    )
                    profiles_added_on_demand.append(profile)

        # add missing profiles
        for profile in profiles_added_on_demand:
            self.profiles[profile.name] = profile

        # now start linking profiles
        for name, profile in self.profiles.items():
            for prop_name, linked_profile_name in profile.find_linked_profiles():
                linked_profile = self.profiles[linked_profile_name]
                profile.link_profile(prop_name, linked_profile)

    def subsample_all(self):
        for name, profile in sorted(self.profiles.items()):
            profile.subsample()

    def print_tree(self):
        empty_profiles = {}

        print("** General info **")
        print(f"Number of all profiles: {len(self.profiles)}")
        print("")

        print("** All profiles **")
        for profile_name, profile in sorted(
            self.profiles.items(), key=lambda item: item[0].lower()
        ):
            print(profile_name)
        print("")

        print("** Profiles with metadata objects **")
        for profile_name, profile in sorted(
            self.profiles.items(), key=lambda item: len(item[1].meta_objs)
        ):
            if len(profile.meta_objs) == 0:
                empty_profiles[profile_name] = profile
                continue

            print(profile_name, len(profile.meta_objs))
            for prop, linked_profile in profile.linked_profiles.items():
                print("\t", prop, linked_profile.name)
        print("")

        print("** Profiles without metadata objects **")
        for profile_name, profile in empty_profiles.items():
            print(profile_name)

    def get_all_uuids_json(self):
        result = {}

        for profile_name, profile in self.profiles.items():
            if profile.meta_objs:
                result[profile_name] = list(profile.meta_objs.keys())
            else:
                result[profile_name] = []

        return result
