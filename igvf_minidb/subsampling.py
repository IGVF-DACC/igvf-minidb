import logging
import math
import random
import requests

from igvf_minidb.connection import get
from urllib.parse import urlencode


logger = logging.getLogger(__name__)

# search_query example:
# "search/?type=Experiment&assay_title=Mint-ChIP-seq&limit=10&field=accession&format=json"
SEARCH_LIMIT = "all"
SEARCH_FIELD = "uuid"
SUBSAMPLING_RANDOM_SEED = 17


class Subsampling:
    def __init__(
        self,
        profile_name,
        search_parameters,
        subsampling_rate=0.0,
        subsampling_min=1
    ):
        self.profile_name = profile_name

        if search_parameters:
            self.query_params = search_parameters
        else:
            self.query_params = {}

        self.query_params.update({
            "format": "json",
            "frame": "object",
            "type": profile_name,
            "limit": SEARCH_LIMIT,
            "field": SEARCH_FIELD,
        })

        self.subsampling_rate = subsampling_rate if subsampling_rate else 0.0
        self.subsampling_min = subsampling_min if subsampling_min else 0

    def subsample(self):
        """
        Returns a list of subsampled UUIDs
        """
        logger.info(f"Subsampling for {self.query_params}")
        all_uuids = self._get_all_uuids()

        if not all_uuids:
            return []

        num_subsampled = max(
            math.floor(self.subsampling_rate * len(all_uuids)),
            self.subsampling_min
        )

        if num_subsampled:
            random.seed(SUBSAMPLING_RANDOM_SEED)
            subsampled = random.choices(all_uuids, k=num_subsampled)
            logger.info(f"\t{subsampled}")

            return subsampled

    def _get_all_uuids(self):
        """
        Get all UUIDs matching given search condition.
        """
        url_query = "search/?" + urlencode(self.query_params)

        all_uuids = []

        try:
            for item in get(url_query)["@graph"]:
                all_uuids.append(item["uuid"])

        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                logger.info(f"!!!! No UUIDs for profile {self.profile_name}")
            else:
                raise

        return all_uuids
