from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
from os import getenv, listdir, remove
from yaml import full_load
from ftplib import FTP
from time import sleep

# variables
load_dotenv()

PATH_TO_SORTING_FOLDER = Path(getenv("pathToSortingFolder") or "")
SORT_DELAY = int(getenv("sortDelay") or "5")
PREFIX = getenv("prefix") or ""
ALIASES_FILE = getenv("aliasesFile") or ""

FTP_HOST = getenv("ftpHost") or ""
FTP_USER = getenv("ftpUsername") or ""
FTP_PASS = getenv("ftpPassword") or ""
FTP_ROOT_PATH = getenv("ftpRootPath") or ""


@dataclass
class SortableFile:
    path: Path
    name: str # final name (PREFIX-X-X-X-THIS.PART)
    year: str
    subject: str
    folder: str



def extractAliasesFromYaml(ymlFile: str) -> dict[str, str]:
    with open(ymlFile) as fp:
        data = full_load(fp)
    return data

# format:  PREFIX-YEAR-SUBJECT-FOLDER-NAME.EXTENSION
def getSortableFiles() -> list[SortableFile]:
    files: list[SortableFile] = []
    aliases = extractAliasesFromYaml(ALIASES_FILE)

    for file in listdir(PATH_TO_SORTING_FOLDER):
        if not file.startswith(PREFIX): continue

        parts = file.split("-")
        if len(parts) < 5: continue
        
        files.append(SortableFile(
            path = PATH_TO_SORTING_FOLDER/file, 
            name = "-".join(parts[4:]),
            year = aliases.get(parts[1]) or parts[1],
            subject = aliases.get(parts[2]) or parts[2],
            folder = aliases.get(parts[3]) or parts[3]
        ))
    
    return files

def createOrGoToDirectory(ftpConnection: FTP, directory: str):
    if directory not in ftpConnection.nlst():
        ftpConnection.mkd(directory)
    ftpConnection.cwd(directory)


def uploadFile(ftpConnection: FTP, file: SortableFile):
    createOrGoToDirectory(ftpConnection, file.year)
    createOrGoToDirectory(ftpConnection, file.subject)
    createOrGoToDirectory(ftpConnection, file.folder)

    try:
        with open(file.path, "rb") as fp: 
            ftpConnection.storbinary('STOR ' + file.name, fp)
        remove(file.path)
        print(f"Successfully sorted {file.path}!")
    except Exception as e: print(f"Couldn't sort {file.path}. Error: {e}")



ftpConnection = FTP(FTP_HOST)
ftpConnection.login(FTP_USER, FTP_PASS)

while True:
    for file in getSortableFiles():
        ftpConnection.cwd(FTP_ROOT_PATH)
        uploadFile(ftpConnection, file)
    
    sleep(SORT_DELAY)




