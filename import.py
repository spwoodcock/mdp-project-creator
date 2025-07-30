"""Import from MdP --> FieldTM."""

import httpx

# TODO batch requests if we need to do this for all of them + a pause between requests
API_LIMIT = 1
SOURCE_URL = f"https://interativobe-mapadasperiferias.cidades.gov.br/api/favela-comunidade-urbana-2022/?format=json&limit={API_LIMIT}"
DEST_URL = "https://api.mdp.fmtm.hotosm.org/projects"
HEADERS = {"X-API-Key": "Bearer YOUR_TOKEN"}

def transform_record(item: dict) -> dict:
    """Transform source record to match your model fields."""
    return {
        "id": item["id"],
        "name": item["nm_fcu"],
        "outline": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [item["bbox"][0], item["bbox"][1]],
                    [item["bbox"][0], item["bbox"][3]],
                    [item["bbox"][2], item["bbox"][3]],
                    [item["bbox"][2], item["bbox"][1]],
                    [item["bbox"][0], item["bbox"][1]],
                ]]
            },
            "properties": {
                "cd_fcu": item["cd_fcu"],
                "total_domicilios": item.get("total_domicilios")
            }
        },
        "short_description": item["nm_mun"],
        "description": f"{item['nm_fcu']} in {item['nm_mun']} ({item['sigla_uf']})",
        "slug": item["cd_fcu"].lower(),
        "location_str": item["nm_mun"],
        "task_split_type": "manual",
        "status": "published",
        "visibility": "private",
    }
    # TODO add all required fields, including project manager

def main():
    # NOTE if we are doing this on a batch, we could optimise significantly
    with httpx.Client(timeout=30.0) as client:
        url = SOURCE_URL
        while url:
            print(f"Fetching {url}")
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
            for item in data["results"]:
                payload = transform_record(item)
                post_resp = client.post(DEST_URL, json=payload, headers=HEADERS)
                if post_resp.status_code != 201:
                    print(f"Failed to insert {item['id']}: {post_resp.text}")
            url = data.get("next")

if __name__ == "__main__":
    main()
