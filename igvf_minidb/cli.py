#!/usr/bin/env python3

import argparse
import glob
import json
import logging

from igvf_minidb.connection import (
    set_username,
    set_password,
    set_endpoint,
    get,
)
from igvf_minidb.profile import (
    Profiles,
)


logger = logging.getLogger(__name__)



def main():
    logging.basicConfig(level = logging.INFO)

    parser = argparse.ArgumentParser(
        description="Mini DB generator"
    )
    parser.add_argument(
        "conf_file",
        help="Configuration JSON file for MiniDB. See README.md for details."
    )
    parser.add_argument(
        "-k", "--key",
        help="Access key ID on the portal."
    )
    parser.add_argument(
        "-s", "--secret",
        help="Secret access key on the portal."
    )

    args = parser.parse_args()

    with open(args.conf_file) as fp:
        conf_json = json.load(fp)

    # set endpoint
    endpoint = conf_json["endpoint"].rstrip("/")
    set_endpoint(endpoint)

    # set credentials
    set_username(args.key)
    set_password(args.secret)

    # get all profiles JSON
    profiles_query = conf_json["profiles_query"]
    profiles_json = get(profiles_query)

    # parse profiles and link them
    subsampling_json = conf_json["subsampling"]
    profiles = Profiles(profiles_json, subsampling_json)
    profiles.link_all_profiles()
    profiles.subsample_all()
    profiles.print_tree()

if __name__ == "__main__":
    main()
