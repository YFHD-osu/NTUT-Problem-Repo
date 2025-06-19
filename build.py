import os
import json
import sys
import uuid

import logging
from datetime import datetime
from typing import Generator, Optional, List, Dict, Any
from pathlib import Path

log_format = "[%(asctime)s] [%(levelname)s] %(message)s"
time_format = "%H:%M:%S"

OUTPUT_ROOT = "output"

logging.basicConfig(
  level=logging.INFO,
  format=log_format,
  datefmt=time_format
)

logger = logging.getLogger(__name__)

class FileManager:
  @staticmethod
  def findJsonFiles(root_dir: str) -> Generator[str, None, None]:
    for dirpath, _, filenames in os.walk(root_dir):
      for file in filenames:
        if file.lower().endswith(".json"):
          yield os.path.join(dirpath, file)

  @staticmethod
  def loadJson(path: str) -> Any:
    if not os.path.exists(path):
      logger.error(f"File {path} does not exist")
      return None

    try:
      with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    except json.JSONDecodeError as e:
      logger.error(f"Json syntax error: {e}")
    except Exception as e:
      logger.error(f"Cannot read file: {e}")

    return None
  
  @staticmethod
  def initOutputFolder(root: str) -> None:
    rootPath = Path(root)
    problems = rootPath.joinpath("problems")
    collections = rootPath.joinpath("collections")

    problems.mkdir(parents=True, exist_ok=True)
    collections.mkdir(parents=True, exist_ok=True)

class Collection:
  def __init__(
    self, 
    name: str, 
    description: str, 
    createDate: datetime,
    directories: Optional[List[Any]],
    problems: List['Problem'],
    uuid: str
  ) -> None:
    self.name = name
    self.description = description
    self.createDate = createDate
    self.directory = directories
    self.problems = problems
    self.uuid = uuid

  @staticmethod
  def fromJson(data: Dict[str, Any]) -> 'Collection':
    name = data["name"]
    description = data["description"]
    createDate = data["createDate"]
    directories: list = data.get("directories", [])

    createDate = datetime.fromtimestamp(createDate / 1000)

    collectionUUID = data.get("uuid", str(uuid.uuid4()))

    problem: list[Problem] = []

    for dir in directories:
      files = FileManager.findJsonFiles(dir)

      jsons = [FileManager.loadJson(f) for f in files]
      
      problem.extend(
        [Problem.fromJson(f, collectionUUID) for f in jsons if f]
      )
      
    return Collection(
      name=name,
      description=description,
      createDate=createDate,
      directories=directories,
      problems=problem,
      uuid=collectionUUID
    )

  def toDict(self) -> dict:
    return {
      "name": self.name,
      "description": self.description,
      "createDate": int(self.createDate.timestamp() * 1000),
      "uuid": self.uuid,
      "problems": [
        p.uuid for p in self.problems
      ]
    }

  def writeToFile(self, root: str):
    r = Path(root)
    folder = r.joinpath("collections")

    with open(folder.joinpath(f"{self.uuid}.json"), "w", encoding="utf-8") as f:
      json.dump(self.toDict(), f, ensure_ascii=False, indent=2)
    logger.info(f"File {folder.joinpath(f"{self.uuid}.json")} saved")

    for problem in self.problems:
      problem.writeToFile(root)


class TestCase:
  def __init__(self, input: List[str], output: List[str]):
    self.input = input
    self.output = output

  def toDict(self) -> dict:
    return {
      "input": self.input,
      "output": self.output
    }

class TestCaseGroup:
  def __init__(self, code_type: int, cases: List[TestCase]):
    self.code_type = code_type
    self.cases = cases

  def toDict(self) -> dict:
    return {
      "codeType": self.code_type,
      "cases": [
        c.toDict() for c in self.cases
      ]
    }

class Problem:
  def __init__(
    self,
    uuid: Optional[str],
    title: str,
    createDate: datetime,
    collections: Optional[List[str]],
    problem: List[str],
    testcase: TestCaseGroup,
    sampleCode: Optional[List[str]]
  ):
    self.uuid = uuid
    self.title = title
    self.create_date = createDate
    self.collections = collections
    self.problem = problem
    self.testcase = testcase
    self.sampleCode = sampleCode

  @staticmethod
  def fromJson(data: dict, parentUUID: str) -> 'Problem':
    problemUUID = data.get("uuid", str(uuid.uuid4()))
    title = data["title"]
    problem = data["problem"]
    createDate = datetime.fromtimestamp(data["createDate"] / 1000)
    collections = data.get("collections", [])
    sampleCode = data.get("sampleCode")

    if not collections:
      collections = [parentUUID]

    testcase = data["testcase"]
    codeType = testcase["codeType"]
    
    cases = [
      TestCase(tc["input"], tc["output"])
      for tc in testcase.get("cases", {})
    ]

    testcase = TestCaseGroup(
      code_type=codeType,
      cases=cases
    )
    
    return Problem(
      uuid=problemUUID,
      title=title,
      createDate=createDate,
      collections=collections,
      problem=problem,
      testcase=testcase,
      sampleCode=sampleCode
    )

  @staticmethod
  def fromFile(path: str, parentUUID: str) -> Optional["Problem"]:
    file = FileManager.loadJson(path)
    
    if not file: return None
    
    return Problem.fromJson(file, parentUUID)

  def toDict(self) -> dict:
    return {
      "uuid": self.uuid,
      "title": self.title,
      "createDate": int(self.create_date.timestamp() * 1000),
      "collections": self.collections,
      "problem": self.problem,
      "testcase": self.testcase.toDict(),
      "sampleCode": self.sampleCode
    }
  
  def writeToFile(self, root: str):
    r = Path(root)
    folder = r.joinpath("problems")

    with open(folder.joinpath(f"{self.uuid}.json"), "w", encoding="utf-8") as f:
      json.dump(self.toDict(), f, ensure_ascii=False, indent=2)

    logger.info(f"File {folder.joinpath(f"{self.uuid}.json")} saved")
  
def main() -> None:
  if len(sys.argv) < 2:
    logger.error("Please specfied the build config json file")
    return
  
  filepath = sys.argv[1]

  # filepath = "build-config.json"

  buildData = FileManager.loadJson(filepath)
  
  if buildData == None:
    return
  
  colData = buildData["collections"]
  
  collections: list[Collection] = []

  for col in colData:
    c = Collection.fromJson(col)
    logger.info(f"Collection '{c.name}' loaded with {len(c.problems)} problem(s)")
    collections.append(c)

  FileManager.initOutputFolder(OUTPUT_ROOT)

  for col in collections:
    col.writeToFile(OUTPUT_ROOT)

  # Write index portal json
  index = {"collections": [ col.uuid for col in collections ]}
  with open(Path(f"{OUTPUT_ROOT}/index.json"), "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

  logger.info("Build complete successfully")
  return

if __name__ == "__main__":
  main()