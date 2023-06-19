# Installation

Install Redis for caching metadata objects retrieved from portal.
```bash
sudo apt-get install redis
````

# Run

Make sure that Redis server is running.
```bash
bin/minidb bin/minidb -j all_encode_profiles.json -s subsampling_strat_def.json  -e "https://test.encodedcc.org" -u $KEY -p $SECRET
```


# Subsampling strategy definition JSON

Example:
```json
{
    "Experiment": {
        "required": {
            "accession": ["ENCSR000EJD"],
            "uuid": []
        },
        "subsample": {
            "rate": 0.001
        }
    },
    "Gene": {
        "required": {
            "all": true
        }
    },
    "Award": {
        "required": {
            "all": true
        }
    },
    "Lab": {
        "subsample": {
            "rate": 0.01
        }
    }
}
```