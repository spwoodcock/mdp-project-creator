"""Import from MdP --> FieldTM."""

import httpx

API_LIMIT = 1
ORGANISATION_ID = 1
SOURCE_URL = f"https://interativobe-mapadasperiferias.cidades.gov.br/api/favela-comunidade-urbana-2022/?format=json&limit={API_LIMIT}"
CREATE_PROJECT_URL = "https://api.mdp.fmtm.hotosm.org/projects/stub"
EDIT_PROJECT_URL = f"https://api.mdp.fmtm.hotosm.org/projects?org_id={ORGANISATION_ID}"
HEADERS = {"X-API-Key": "Bearer YOUR_TOKEN"}

def create_project_data(mdp_project: dict) -> dict:
    """Transform MDP data into FieldTM project stub data."""
    return {
        "name": mdp_project["nm_fcu"],
        "outline": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [mdp_project["bbox"][0], mdp_project["bbox"][1]],
                    [mdp_project["bbox"][0], mdp_project["bbox"][3]],
                    [mdp_project["bbox"][2], mdp_project["bbox"][3]],
                    [mdp_project["bbox"][2], mdp_project["bbox"][1]],
                    [mdp_project["bbox"][0], mdp_project["bbox"][1]],
                ]]
            },
            "id": mdp_project["id"],
            "properties": {
                "cd_fcu": mdp_project["cd_fcu"],
                "total_domicilios": mdp_project.get("total_domicilios")
            }
        },
        "short_description": mdp_project["nm_mun"],
        "description": f"{mdp_project['nm_fcu']} in {mdp_project['nm_mun']} ({mdp_project['sigla_uf']})",
        "status": "PUBLISHED",
        "hashtags": ["mdp", "mapa-das-periferias"],
        "task_split_type": "manual",
        "visibility": "private",
    }

def update_project_data(mdp_project: dict) -> dict:
    """Transform MDP data into FieldTM project full data."""
    return {
        "task_split_type": "manual",
        "visibility": "private",
    }

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
                payload = create_project_data(item)

                # 1. Basic project details
                new_project = client.post(CREATE_PROJECT_URL, json=payload, headers=HEADERS)
                if new_project.status_code > 204:
                    print(f"Failed to insert {item['id']}: {new_project.text}")
                    # Skip edit project
                    continue
                new_project_id = new_project.json().get("id")

                # 2. Add remaining project details
                updated_project = client.patch(f"{EDIT_PROJECT_URL}?project_id={new_project_id}", json=payload, headers=HEADERS)
                if updated_project.status_code > 204:
                    print(f"Failed to insert {item['id']}: {updated_project.text}")

                # 3. TODO Upload survey
                # 4. TODO Upload data
                # 5. TODO Upload split boundaries
                # 6. TODO Trigger project finalisation

            # TODO when we run this for real, remove the break to interate
            break
            # TODO send these in asyncio.gather batches, with a sleep interval between
            url = data.get("next")

if __name__ == "__main__":
    main()
