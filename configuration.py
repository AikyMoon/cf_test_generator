from __future__ import annotations
from random import choice, randint
from pprint import pprint
from typing import NewType
from termcolor import colored

import json
import os



class BaseGenerator:
    """
    Общий класс генераторов
    """
    generator_type = None


    def __init__(self) -> None:
        self.last_state = None

    def generate(self) -> None:
        pass


class IntGenerator(BaseGenerator):
    """
    Класс генератора чисел
    """
    generator_type = int

    def __init__(self, min_value: int, max_value: int) -> None:
        self.min_value = min_value
        self.max_value = max_value
        super().__init__()
        
    

    def generate(self) -> int:
        self.last_state = randint(self.min_value, self.max_value)
        return self.last_state


    def __str__(self) -> str:
        return f"Числа на интервале [{self.min_value}, {self.max_value}]"
    

    def __repr__(self) -> str:
        return f"Числа на интервале [{self.min_value}, {self.max_value}]"
    


class ListGenerator(BaseGenerator):
    """
    Класс генератора последовательностей
    """
    generator_type: type = list[int]


    def __init__(self, element_generator: BaseGenerator, len_generator: IntGenerator) -> None:
        self.element = element_generator
        self.len_generator: IntGenerator = len_generator
        

    def generate(self) -> list:
        return " ".join([str(self.element.generate()) for _ in range(self.len_generator.last_state)])

    def __str__(self) -> str:
        return f"Последовательность чисел. Генератор длины: {self.len_generator}"
    

    def __repr__(self) -> str:
        return f"Последовательность чисел. Генератор длины: {self.len_generator}"
    


class StringGenerator(BaseGenerator):
    """
    Класс генератора строк
    """
    generator_type = str
    

    def __init__(self, valid_chars: str | list[str], len_generator: IntGenerator) -> None:
        self.valid_chars = valid_chars
        self.len_generator: IntGenerator = len_generator


    def generate(self) -> str:
        return "".join((choice(self.valid_chars) for _ in range(self.len_generator.last_state)))
    
    def __str__(self) -> str:
        return f"Последовательность символов: {self.valid_chars}. Генератор длины: {self.len_generator}"
    
    def __repr__(self) -> str:
        return f"Последовательность символов: {self.valid_chars}. Генератор длины: {self.len_generator}"



class Configuration:
    """
    Класс конфигурации
    """
    def __init__(self, config_path: str) -> None:
        self.config_path: str = config_path
        self.config_name: str = None
        self.output_format: str = None
        self.groups: dict[int, dict[str, BaseGenerator]] = {}
        self.__parse()
    

    def __parse(self):
        d = {}

        with open(self.config_path, 'r') as fin:
            d = json.load(fin)

        self.config_name = d["config_name"]

        for key, desc in d["groups"].items():
            self.groups[key] = {}
            for var, var_desc in desc.items():
                if var == "n_samples":
                    self.groups[key][var] = var_desc
                    continue

                var_type = var_desc["type"]
                subdict = {}

                if var_type == "int":
                    subdict["generator"] = IntGenerator(var_desc["min"], var_desc["max"])

                elif var_type == "list_int":
                    len_generator = self.groups[key][var_desc["len"]]["generator"]
                    subdict["generator"] = ListGenerator(IntGenerator(var_desc["min"], var_desc["max"]), len_generator)

                elif var_type == "string":
                    valid_chars = var_desc["valid_chars"]
                    len_generator = self.groups[key][var_desc["len"]]["generator"]
                    subdict["generator"] = StringGenerator(valid_chars, len_generator)


                subdict["type"] = var_type
                self.groups[key][var] = subdict
        
        self.output_format = d["output_format"]
        


class FileGenerator:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath if filepath[-1] == "/" else filepath + "/"

        
    def generate_dump(self, filename: str, values: dict[int, list] | dict[int, list[tuple]]) -> None:
        with open(self.filepath + filename, "w") as fout:
            for _, data in sorted(values.items()):
                
                separators = data["sep"]
                vars = data["data"]

                for data_line in vars:
                    line = ""
                    if separators:
                        for i in range(len(separators)):
                            line += str(data_line[i]) + separators[i]
                        line += str(data_line[-1])
                    else:
                        line += " ".join(map(str, data_line))
                    fout.write(line + "\n")
            


class TestcaseGenerator:
    def __init__(self, conf: Configuration, test_dir_path: str) -> None:
        self.conf: Configuration = conf
        self.test_dir_path: str = test_dir_path if test_dir_path[-1] != "/" else test_dir_path[:-1]
        self.output_format: dict = conf.output_format
        self.task_name = self.conf.config_name
        if not os.path.exists(f"{test_dir_path}/{self.task_name}/"):
            os.mkdir(f"{test_dir_path}/{self.task_name}/")
            self.test_dir_path = f"{test_dir_path}/{self.task_name}/"
        else:
            self.test_dir_path = f"{self.test_dir_path}/{self.task_name}"
        
        self.file_generator = FileGenerator(self.test_dir_path)
        
        


    def generate(self) -> None:
        for group, desc in self.conf.groups.items():
            for cur_sample in range(desc["n_samples"]):
                output = {}

                for line_num, output_desc in self.output_format.items():
                    vars = []

                    if output_desc["repeat"] is None:
                        for var in output_desc["vars"]:
                            vars.append(desc[var]["generator"].generate())
                        vars = [tuple(vars)]

                    else:
                        cycle_var = desc[output_desc["repeat"]]["generator"].last_state
                        samples = []

                        for _ in range(cycle_var):
                            samples = []
                            for var in output_desc["vars"]:
                                samples.append(desc[var]["generator"].generate())
                            
                            vars.append(tuple(samples))
                    
                    output[int(line_num)] = {"sep": output_desc["sep"], "data": vars}
                    # pprint(output)
                
                
                # print(f"{title:-^100}")

                filename = self.__get_filename(group, cur_sample)
                title = f"{filename} успешно сгенерирован"
                print(colored(title, "green"))
                self.file_generator.generate_dump(filename, output)


    def __get_filename(self, group: int, sample: int) -> str:
        return f"{self.task_name}_{group}_{sample}.txt"
    
    
TESTCASES_DIR = "/Users/aikymoon/Desktop/codeforces_custom_tasks/tests/"

conf = Configuration("/Users/aikymoon/Desktop/codeforces_custom_tasks/tests_configurations/test.json")
gen = TestcaseGenerator(conf, TESTCASES_DIR)
gen.generate()