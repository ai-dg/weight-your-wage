from pathlib import Path

import kagglehub
import shutil


DATASET_HANDLE = "edoardogalli/stack-overflow-annual-developer-survey-2025"


def download_survey_file(target_dir: str = "./srcs/model/datasets", filename: str = "survey_results_public.csv") -> Path:
    target_folder = Path(target_dir)
    target_folder.mkdir(parents=True, exist_ok=True)
    dataset_path = target_folder / filename

    if dataset_path.exists():
        return dataset_path

    print("Downloading dataset file from Kaggle...")
    tmp_path = kagglehub.dataset_download(DATASET_HANDLE, path=filename)
    shutil.copy2(tmp_path, dataset_path)
    print(f"Saved file to {dataset_path}")
    return dataset_path

def main():
    download_survey_file()


if __name__ == "__main__":
    main()