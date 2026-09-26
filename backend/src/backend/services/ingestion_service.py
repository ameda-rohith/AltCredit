import json
import csv
from pathlib import Path


def load_json(file_path: str):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def load_csv(file_path: str):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        return list(reader)


def load_data(file_path: str):

    extension = Path(file_path).suffix.lower()

    if extension == ".json":
        return load_json(file_path)

    if extension == ".csv":
        return load_csv(file_path)

    raise ValueError(
        "Unsupported file format. "
        "Only CSV and JSON are supported."
    )