# Installation

Install Redis for caching metadata objects retrieved from portal.
```bash
sudo apt-get install redis
````

# Run

Make sure that Redis server is running. Get `ACCESS_KEY` and `ACCESS_KEY_SECRET` pair from portal's Profile menu.
```bash
bin/minidb CONF_JSON_FILE -k ACCESS_KEY -s ACCESS_KEY_SECRET 
```


# Configuration JSON file

Three items should be defined:
- `"endpoint"`: Endpoint
- `"profiles_query"`: URL query to get all profiles.
- `"subsampling"`: Subsampling strategies



Example:
```json
{
    "endpoint": "https://www.encodeproject.org",
    "profiles_query": "profiles/?format=json&frame=object",
    "subsampling":
    {
        "CollectionSeries":
        [
            {
                "subsampling_min": 1
            }
        ],
        "AccessKey":
        [
            {
                "subsampling_min": 1
            }
        ],
        "Cart":
        [
            {
                "subsampling_min": 1
            }
        ],
        "AntibodyCharacterization":
        [
            {
                "subsampling_min": 1
            }
        ],
        "Experiment":
        [
            {
                "search_parameters":
                {
                    "assay_title": "TF ChIP-seq"
                },
                "subsampling_min": 1,
                "subsampling_rate": 0.00001
            },
            {
                "search_parameters":
                {
                    "assay_title": "Histone ChIP-seq"
                },
                "subsampling_min": 1,
                "subsampling_rate": 0.00001
            }
        ]
    }
}
```