import os, requests, enum
from tqdm import tqdm
import urllib
import tempfile
from urllib.error import HTTPError
from urllib.request import *

from .geofabrik_sources import (
        Africa,
        Antarctica,
        Asia,
        AustraliaOceania,
        Europe,
        NorthAmerica,
        SouthAmerica,
        CentralAmerica,
        Brazil,
        Canada,
        France,
        Germany,
        GreatBritain,
        Italy,
        Japan,
        Netherlands,
        Poland,
        Russia,
        USA,
        SubRegions,
    )

class DataSources:
    def __init__(self):
        self.africa = Africa()
        self.antarctica = Antarctica()
        self.asia = Asia()
        self.australia_oceania = AustraliaOceania()
        self.europe = Europe()
        self.north_america = NorthAmerica()
        self.south_america = SouthAmerica()
        self.central_america = CentralAmerica()
        self.subregions = SubRegions()

        self.available = {
            "africa": self.africa.available,
            "antarctica": self.antarctica.available,
            "asia": self.asia.available,
            "australia_oceania": self.australia_oceania.available,
            "central_america": self.central_america.available,
            "europe": self.europe.available,
            "north_america": self.north_america.available,
            "south_america": self.south_america.available,
            "subregions": self.subregions.available,
        }

        # Gather all data sources
        # Keep hidden to avoid encouraging iteration of the whole
        # world at once which most likely would end up
        # in memory error / filling the disk etc.
        self._all_sources = [
            k for k in self.available.keys() if k not in ["subregions"]
        ]

        for source, available in self.available.items():
            self._all_sources += available

        for subregion in self.subregions.available:
            self._all_sources += self.subregions.__dict__[subregion].available

        self._all_sources = [src.lower() for src in self._all_sources]      
        self._all_sources = list(set(self._all_sources))

class UNIT(enum.Enum):
    BYTES = 1
    KB = 2
    MB = 3
    GB = 4

def convert_unit(size_in_bytes, unit):
    if unit == UNIT.KB:
        return size_in_bytes / 1024
    elif unit == UNIT.MB:
        return size_in_bytes / (1024 * 1024)
    elif unit == UNIT.GB:
        return size_in_bytes / (1024 * 1024 * 1024)
    else:
        return size_in_bytes


def get_file_size(file_name, size_type=UNIT.MB):
    size = os.path.getsize(file_name)
    return round(convert_unit(size, size_type), 2)


def download(url, filename, update, target_dir):
    if target_dir is None:
        temp_dir = tempfile.gettempdir()
        target_dir = os.path.join(temp_dir, "mbtiles_util")
    else:
        if not os.path.isdir(target_dir):
            raise ValueError(f"The provided directory does not exist: " f"{target_dir}")

    filepath = os.path.abspath(os.path.join(target_dir, os.path.basename(filename)))

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Check if file exists
    file_exists = False
    if os.path.exists(filepath):
        file_exists = True

    if update and file_exists:
        os.remove(filepath)

    # Download data to temp if it does not exist or if update is requested
    if update or file_exists is False:
        try:
            filepath, msg = urllib.request.urlretrieve(url, filepath)
        except HTTPError:
            raise ValueError(
                f"PBF-file '{url}' is temporarily unavailable. " f"Try again later."
            )
        except Exception as e:
            raise e

        filesize = get_file_size(filepath)
        if filesize == 0:
            raise ValueError(
                f"PBF-file '{filename}' from the provider was empty. "
                "This is likely a temporary issue, try again later."
            )
        print(
            f"Downloaded Protobuf data '{os.path.basename(filepath)}' "
            f"({filesize} MB) to:\n'{filepath}'"
        )
    return filepath

# Initialize DataSources
sources = DataSources()
available = {
    "regions": {
        k: v for k, v in sources.available.items() if k not in ["subregions"]
    },
    "subregions": sources.subregions.available
}


def retrieve(data, update, directory):
    # return download(
    #     url=data["url"], filename=data["name"], update=update, target_dir=directory
    # )
    return download_file(data["url"], os.getcwd())


def search_source(name):
    for source, available in sources.available.items():
        if isinstance(available, list):
            if name in available:
                return sources.__dict__[source].__dict__[name]
        elif isinstance(available, dict):
            # Sub-regions should be looked one level further down
            for subregion, available2 in available.items():
                if name in available2:
                    return sources.subregions.__dict__[subregion].__dict__[name]
    raise ValueError(f"Could not retrieve url for '{name}'.")


def get_data(dataset, update=False, directory=None):
    """
    Get the path to a PBF data file, and download the data if needed.

    Parameters
    ----------
    dataset : str
        The name of the dataset. Run ``pyrosm.data.available`` for
        all available options.

    update : bool
        Whether the PBF file should be downloaded/updated if the dataset
        with the same name exists in the temp.

    directory : str (optional)
        Path to a directory where the PBF data will be downloaded.
        (does not apply for test data sets bundled with the package).
    """
    if not isinstance(dataset, str):
        raise ValueError(f"'dataset' should be text. Got {dataset}.")
    dataset = dataset.lower().strip()

    if dataset in sources._all_sources:
        return retrieve(search_source(dataset), update, directory)

    elif dataset.replace(" ", "") in sources._all_sources:
        return retrieve(search_source(dataset.replace(" ", "")), update, directory)

    # Users might pass country names without underscores (e.g. North America)
    elif dataset.replace(" ", "_") in sources._all_sources:
        return retrieve(search_source(dataset.replace(" ", "_")), update, directory)

    # Users might pass country names with dashes instead of underscores (e.g. canary-islands)
    elif dataset.replace("-", "_") in sources._all_sources:
        return retrieve(search_source(dataset.replace("-", "_")), update, directory)

    else:
        msg = "The dataset '{data}' is not available. ".format(data=dataset)
        msg += "Available datasets are {}".format(", ".join(sources._all_sources))
        raise ValueError(msg)

####### Test
def download_file(url, save_to) :
    # url     - url of downloadable file
    # save_to - directory to save the file to
    
    print("Downloading from:", url)       
    req = requests.get(url, stream=True)
    if 'Content-Disposition' in req.headers:
        filename = req.headers['Content-Disposition'].split("filename=")[1]
    else:
        filename = os.path.basename(url)
    os.chdir(save_to)

    if req.status_code == 200:
        # Calculate the total file size in bytes
        total_size = int(req.headers.get('content-length', 0))
        # Open the file in binary write mode
        with open(filename, 'wb') as file:
            # Use tqdm to show the progress bar
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename, ncols=100) as pbar:
                # Iterate over the content of the response in chunks
                for chunk in req.iter_content(chunk_size=8192):
                    if chunk:
                        # Write the chunk to the file
                        file.write(chunk)
                        # Update the progress bar with the size of the chunk
                        pbar.update(len(chunk))
        file.close()
        print(filename, "has been downloaded to", save_to)
    #______________________________________________________________________________

def main():
    save_to = os.getcwd()
    get_data("yemen", update=True,directory = save_to)
    # print (available)
    # print (available.keys())
    # url = "https://github.com/udsleeds/openinfra/releases/download/v0.2/Leeds_06_06_22.osm.pbf"
    # # Change this to your desired download directory.
    # save_to = os.getcwd()
    # download_file(url, save_to)

if __name__ == "__main__":
    main()

