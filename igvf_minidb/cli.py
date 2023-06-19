#!/usr/bin/env python3

import argparse
import glob
import logging
import os

from igvf_minidb.profile import (
    Profile,
    Profiles,
)
from igvf_minidb.subsampling import (
    SubsamplingStrat
)
from igvf_minidb.connection import (
    set_username,
    set_password,
    set_endpoint,
)

logger = logging.getLogger(__name__)


def main():

    parser = argparse.ArgumentParser(
        description="Mini DB generator"
    )
    parser.add_argument(
        "-j", "--profiles-json-file",
        required=True,
        help=(
            "Profiles JSON file, which can be snapshotted with the following command:\n"
            "- ENCODE: curl 'https://www.encodeproject.org/profiles/?format=json&frame=object'> encode_profiles.json\n"
            "- IGVF: curl 'https://api.data.igvf.org/profiles/?format=json&frame=object'> igvf_profiles.json"
        )
    )

    parser.add_argument(
        "-s", "--subsampling-strat-def-json",
        required=True,
        help=(
            "Subsampling strategy JSON file. "
            "This file is used to defined how to subsample objects in each profile. "
            "See documentation for details."
        )
    )

    parser.add_argument(
        "-e", "--endpoint",
        required=True,
        help=(
            "Endpoint (e.g. https://www.encodeproject.org, https://api.data.igvf.org)\n"
            "Make sure to have prefix api. for IGVF endpoints."
        )
    )
    parser.add_argument(
        "-u", "--username",
        help="Username (key)."
    )
    parser.add_argument(
        "-p", "--password",
        help="Password (secret)."
    )

    args = parser.parse_args()

    set_endpoint(args.endpoint)
    set_username(args.username)
    set_password(args.password)

    profiles = Profiles.load_from_profiles_json_file(args.profiles_json_file)
    profiles.link_all_profiles()

    subsampling_strat = SubsamplingStrat(profiles, args.subsampling_strat_def_json)
    subsampling_strat.subsample()

    profiles.print_tree(hideEmptyProfile=True)

if __name__ == "__main__":
    main()
