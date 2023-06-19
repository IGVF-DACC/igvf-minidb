""" subsample strategy definition file format (JSON)
{
    profile_name: {
        # any required accessions or uuid's
        required: {
            # special key "all" to include all objects under a profile (e.g. gene)
            # if "all" then do not get metadata from server and don't do DFS
            all: boolean,
            accession: [
            ],
            uuid: [
            ]
        }
    }    
}
"""

import json
import os
import logging

from igvf_minidb.connection import get
from igvf_minidb.profile import (
    Profile,
    Profiles,
)


logger = logging.getLogger(__name__)


class SubsamplingStrat:
    def __init__(self, profiles, subsampling_strat_def_json_file):
        """
        Args:
            profiles:
                Dict of {profile_name: `Profile` object}
            subsampling_strat_def_json_file:
                strat JSON file
        """
        self.profiles = profiles.profiles

        with open(subsampling_strat_def_json_file) as fp:
            self.strat = json.load(fp)

    def subsample(self):
        """
        Subsample based on Mini DB definition JSON
        This JSON file defines how to subsample each profile        
        """
        for profile_name, strat in self.strat.items():

            profile = self.profiles[profile_name]

            if "required" in strat:
                required = strat["required"]

                identifying_vals = []
                if "accession" in required:
                    identifying_vals += required["accession"]
                if "uuid" in required:
                    identifying_vals += required["uuid"]

                for identifying_val in identifying_vals:
                    meta_obj = get(f"{profile.name}/{identifying_val}")
                    profile.add_meta_obj(meta_obj)
