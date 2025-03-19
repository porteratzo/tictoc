import os


class BaseSaver:
    def __init__(self, benchmarker, file: str = "performance/base") -> None:
        self.file = file
        self.folder = os.path.join(*file.split("/")[:-1])
        self.benchmarker = benchmarker
