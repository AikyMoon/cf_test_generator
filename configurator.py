from __future__ import annotations
from random import choice, randint
from pprint import pprint
from typing import NewType
import json

# # типы данных генераторов
# int_generator = NewType()


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
        return (str(self.element.generate()) for _ in range(self.len_generator.last_state))

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
        


class TestGenerator:
    def __init__(self, conf: Configuration, test_dir_path: str) -> None:
        self.conf: Configuration = conf
        self.test_dir_path: str = test_dir_path
        self.output_format: dict = conf.output_format


    def generate(self) -> None:
        # with open("/Users/aikymoon/Desktop/codeforces_custom_tasks/tests_configurations/test.txt", 'w') as fout:
        for group, desc in self.conf.groups.items():
            for output_desc in self.output_format.values():
                if output_desc["repeat"] is None:
                    vars = []
                    for var in output_desc["vars"]:
                        vars.append(desc[var]["generator"].generate())

                    print(vars)
                else:
                    cycle_vars = desc[output_desc["repeat"]]["generator"].generate()
                    


            #     print(group, output_desc)
                # pprint(desc)
                print()
            print("-" * 100)


    def __get_filename(task_name: str, group: int, sample: int) -> str:
        return f"{task_name}_{group}_{sample}.txt"
    

conf = Configuration("/Users/aikymoon/Desktop/codeforces_custom_tasks/tests_configurations/test2.json")
# pprint(conf.groups)
gen = TestGenerator(conf, "aaaaaa")

gen.generate()