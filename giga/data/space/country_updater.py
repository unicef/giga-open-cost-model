
import ipywidgets as widgets
import pandas as pd
import os
import json
import subprocess
from IPython.display import display
from io import StringIO

from typing import List
from giga.data.web.giga_api_client import GigaAPIClient
from giga.data.store.stores import COUNTRY_DATA_STORE as data_store
from giga.utils.globals import COUNTRY_DEFAULT_RELATIVE_DIR
from giga.schemas.school import GigaSchoolTable, GigaSchool
from giga.schemas.cellular import CellTowerTable
from giga.schemas.geo import UniqueCoordinateTable
from giga.schemas.conf.country import CountryDefaults
from giga.app.config import get_registered_countries
from giga.viz.notebooks.cost_estimation_parameter_input import CostEstimationParameterInput
from giga.utils.progress_bar import progress_bar as pb

GIGA_AUTH_TOKEN = os.environ.get("GIGA_AUTH_TOKEN", "")



class CountryUpdateRequest:
    """Represents a request to add or update one country."""
    country_defaults: CountryDefaults
    cellular: widgets.FileUpload = None
    fiber: widgets.FileUpload = None
    schools_supplemental: widgets.FileUpload = None

    def column_check_error_str(self, file: StringIO, req_cols: List[str]) -> str:
        df = pd.read_csv(file)
        err_str = None
        for col in req_cols:
            if col in df.columns:
                continue
            if err_str is None:
                err_str = f"Missing required column(s): {col}"
            else:
                err_str = f"{err_str}, {col}"
        return err_str

    def validation_error_str(self) -> str:
        """Returns None if request is valid, otherwise returns validation error message."""
        # Validate cellular tower locations.
        if len(self.cellular.value) != 0:
            try:
                cell_data = CellTowerTable.from_frame(
                    pd.read_csv(self.file_string_io(self.cellular)))
                if len(cell_data.towers) == 0:
                    return "Provided cellular data was empty."
            except Exception as e:
                return f"Error loading cell data: {e}"
        # Validate fiber tower locations.
        if len(self.fiber.value) != 0:
            fiber_err = self.column_check_error_str(self.file_string_io(self.fiber),
                    ["coordinate_id", "lat", "lon"])
            if fiber_err is not None:
                return fiber_err
        # Validate supplemental school data
        if len(self.schools_supplemental.value) != 0:
            sup_data = pd.read_csv(self.file_string_io(self.schools_supplemental))
            supp_err = CountryUpdater.validate_supplemental_inputs(sup_data)
            if supp_err is not None:
                return supp_err
        return None
    
    def is_creating_new(self) -> bool:
        return not self.country_name in self.registered_countries
    
    @property
    def country_name(self) -> str:
        return self.country_defaults.data.country
    
    @property
    def registered_countries(self):
        if self.registered_countries_ is None:
            self.registered_countries_ = get_registered_countries()
        return self.registered_countries_
    registered_countries_ = None

    def file_contents(self, upload_widget: widgets.FileUpload) -> StringIO:
        if len(upload_widget.value) == 0:
            return None
        content = upload_widget.value[0]['content']
        return content.tobytes()
    
    def file_string_io(self, upload_widget: widgets.FileUpload) -> StringIO:
        return StringIO(self.file_contents(upload_widget).decode('utf-8'))
    
    @property
    def default_paths(self):
        return {
            self.cellular: f"/workspace/{self.country_name}/cellular.csv",
            self.fiber: f"/workspace/{self.country_name}/fiber.csv",
            self.schools_supplemental: f"/workspace/{self.country_name}/schools_supplemental.csv"
        }
    
    def set_country_defaults(self, inputs: CostEstimationParameterInput, country_name, country_code, lat_lon):
        defaults_dict = {
            "data": {
                "country": country_name,
                "country_code": country_code,
                "workspace": "workspace",
                "school_file": "schools.csv",
                "fiber_file": "fiber.csv",
                "cellular_file": "cellular.csv",
                "cellular_distance_cache_file": "cellular_cache.json",
                "p2p_distance_cache_file": "p2p_cache.json",
                "country_center": lat_lon
            },
            "model_defaults": {
                "scenario": inputs.scenario_parameters(),
                "fiber": inputs.fiber_parameters(),
                "satellite": inputs.satellite_parameters(),
                "cellular": inputs.cellular_parameters(),
                "p2p": inputs.p2p_parameters(),
                "electricity": inputs.electricity_parameters()
            }
        }
        self.country_defaults = CountryDefaults.from_defaults(defaults_dict, full_paths=False)

    def attempt(self) -> bool:
        # TODO make name safe
        return CountryUpdater.update(self)
        

class CountryUpdater:
    """Exposes static methods to update countries in GCS."""
    @staticmethod
    def update(req: CountryUpdateRequest) -> bool:
        val_err = req.validation_error_str()
        if val_err is not None:
            print(f"Validation error: {val_err}")
            return False
        
        # Fetch raw schools using the Giga API
        print(f"Fetching updated schools for {req.country_name}. This may take a moment...")
        raw_schools = CountryUpdater.get_raw_schools(req)
        print(f"Found {len(raw_schools)} schools.")
        school_err = CountryUpdater.validate_raw_school_inputs(raw_schools)
        assert school_err is None, school_err

        # Write country defaults.

        print("Writing country data to file...")
        defaults_file_path = CountryUpdater.conf_path(req.country_name)
        data_store.write_file(defaults_file_path, req.country_defaults.to_json())
        n_updated = 1

        for btn, path in req.default_paths.items():
            if len(btn.value) == 0:
                if data_store.file_exists(path):
                    print(f"Skipping {btn.description}, as no file was uploaded and one exists.")
                    continue
                print(f"Writing empty file for {btn.description}, as one does not exist.")
                data_store.write_file(path, "")
                continue
            content = req.file_contents(btn)
            data_store.write_file(path, content)
            print(f"Updated {btn.description} at {path}")
            n_updated += 1


        print(f"Merging schools with supplemental information for this country...")
        if len(req.schools_supplemental.value) > 0:
            # Merge with provided supplemental info (already validated)
            supp_data = pd.read_csv(req.file_string_io(req.schools_supplemental))
        else:
            # Will be empty frame for new schools
            supp_data = CountryUpdater.get_current_supp_data(req.country_name)
        schools = CountryUpdater.get_countries_with_supp_data(raw_schools, supp_data)

        schools_path = f"/workspace/{req.country_name}/schools.csv"
        print(f"Writing updated schools dataset to {schools_path}...")
        with data_store.open(schools_path, "w") as f:
            schools.to_csv(f)
        
        electricity_path = f"/workspace/{req.country_name}/electricity.csv"
        print(f"Writing electricity cache to {electricity_path}")
        electricity = supp_data.rename(columns={"electricity":"has_electricity"})[["giga_id_school", "has_electricity"]]
        with data_store.open(electricity_path, "w") as f:
            electricity.to_csv(f, index=False)
        n_updated += 2
        print(f"\nIn total, updated {n_updated} files for {req.country_name}.")
        return True

    @staticmethod
    def validate_raw_school_inputs(raw_schools: List[GigaSchool]) -> str:
        if len(raw_schools) == 0:
            return "No schools found for country, perhaps there is an issue with the project connect API"
        return None
    
    @staticmethod
    def get_current_supp_data(country: str):
        path = f"/workspace/{country}/schools_supplemental.csv"
        try:
            with data_store.open(path) as file:
                sup = pd.read_csv(file)
                supp_err = CountryUpdater.validate_supplemental_inputs(sup)
                assert supp_err is None, supp_err
                return sup
        except:
            return pd.DataFrame(
                columns=["giga_id_school", "electricity", "fiber", "num_students", "coverage_type"])
        
    @staticmethod
    def delete(country: str):
        dir = f"/workspace/{country}/"
        data_store.rmdir(dir)
        data_store.remove(CountryUpdater.conf_path(country))
        
    @staticmethod
    def update_cache(country: str):
        display("Updating cache -- please stay on this page until the process is complete.")
        out = widgets.Output()
        after = widgets.Output()
        display(out, after)
        update_scripts = [
            "bin/create_fiber_distance_cache",
            "bin/create_cellular_distance_cache",
            "giga/app/create_p2p_distance_cache.py"
        ]
        with out:
            for script in pb(update_scripts):
                path = os.path.join("..", "..", script)
                with after:
                    subprocess.run(["python", path, "-w", f"/workspace/{country}/"])
            display("Complete!")

    @staticmethod
    def validate_supplemental_inputs(sup) -> str:
        """
        Validates supplemental school inputs.
        Note that it expects supplemental input format
        (before coercion into standard schools dataset).

        Returns validation error string, or None if input is valid.
        """
        if not all(
            k in sup.keys()
            for k in [
                "giga_id_school",
                "electricity",
                "fiber",
                "num_students",
                "coverage_type",
            ]
        ):
            return "Supplemental data is missing required columns."
        return None
    
    @staticmethod
    def conf_path(country_name: str):
        return f"{COUNTRY_DEFAULT_RELATIVE_DIR}/{country_name}.json"
    
    @staticmethod
    def get_electricity_lookup(supp_data):
        """Returns a dataframe with only electricity information"""
        return {
            str(row["giga_id_school"]): bool(row["electricity"])
            for _, row in supp_data.iterrows()
        }


    @staticmethod
    def get_raw_schools(req: CountryUpdateRequest):
        return GigaAPIClient(GIGA_AUTH_TOKEN).get_schools_by_code(
            req.country_defaults.data.country_code)

    @staticmethod
    def get_countries_with_supp_data(raw_schools, sup):
        """
        Attempts to merge the provided supplemental school info into
        the provided raw schools dataset.

        Validates provided raw school inputs and supplemental inputs

        Returns merged school dataframe with updated supplemental information
        """
        # Validation
        school_err = CountryUpdater.validate_raw_school_inputs(raw_schools)
        assert school_err is None, school_err
        sup_err = CountryUpdater.validate_supplemental_inputs(sup)
        assert sup_err is None, sup_err

        # Rename supplemental columns
        sup = sup[
            ["giga_id_school", "electricity", "fiber", "num_students", "coverage_type"]
        ]
        sup = sup.rename(
            columns={
                "giga_id_school": "giga_id",
                "electricity": "has_electricity",
                "fiber": "has_fiber",
                "coverage_type": "cell_coverage_type",
            }
        )

        # Get raw schools as a data frame
        table = GigaSchoolTable(schools=raw_schools)
        frame = table.to_data_frame()

        # update the values in base frame with supplemental data
        sup = sup.set_index("giga_id")
        frame = frame.set_index("giga_id")
        frame.update(sup)
        frame = frame.reset_index()
        frame["num_students"] = frame["num_students"].apply(
            lambda x: int(0 if x is None else x)
        )
        # make connectivity boolean
        frame["connected"] = frame["connectivity_status"].apply(
            lambda x: True if (x == "Good" or x == "Moderate") else False
        )
        # update names to match base schema
        return frame.rename(
            columns={
                "giga_id": "giga_id_school",
                "school_zone": "environment",
                "connectivity_status": "connectivity_speed_status",
            }
        )
